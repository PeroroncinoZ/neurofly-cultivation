"""Read-only, separate-process 3D skeleton viewer. See visualization_3d.md."""
import math
import multiprocessing as mp
from pathlib import Path
import queue
import time

from brain.visualization_context import load_context, CONTEXT_COLOR

SKELETON_DIR = Path(__file__).resolve().parent / 'morphology'
SELECTED_NEURONS = {
    720575940630770042: 'DM1_lPN left',
    720575940619071005: 'DM1_lPN right',
    720575940624547622: 'APL left',
    720575940613583001: 'APL right',
    720575940609959637: 'MBON32 left',
    720575940638526278: 'MBON32 right',
    720575940604737708: 'DNa02 right',
    720575940629327659: 'DNa02 left',
}
COLORS = [(90, 180, 255), (255, 160, 70), (110, 230, 160), (230, 110, 190),
          (180, 150, 255), (240, 220, 90), (80, 230, 230), (255, 110, 110)]


def load_skeleton(path, root_id=None):
    """Parse SWC without rescaling coordinates; skip/report malformed rows.

    Parents are resolved after all rows, so forward references are supported.
    Invalid links are omitted without discarding valid node coordinates.
    """
    nodes, metadata, parents, warnings = {}, {}, {}, []
    skipped = 0
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.split('#', 1)[0].split()
            if not fields:
                continue
            try:
                if len(fields) != 7:
                    raise ValueError('expected seven SWC fields')
                node_id, kind = int(fields[0]), int(fields[1])
                xyz = tuple(float(v) for v in fields[2:5])
                radius, parent = float(fields[5]), int(fields[6])
                if node_id <= 0 or node_id in nodes or kind < 0:
                    raise ValueError('invalid or duplicate node ID/type')
                if not all(math.isfinite(v) for v in (*xyz, radius)) or radius < 0:
                    raise ValueError('nonfinite coordinate/radius or negative radius')
                if parent != -1 and (parent <= 0 or parent == node_id):
                    raise ValueError('invalid parent ID')
            except ValueError as exc:
                warnings.append(f'line {line_number}: {exc}')
                skipped += 1
                continue
            nodes[node_id] = xyz
            metadata[node_id] = {'type': kind, 'radius': radius, 'parent_id': parent}
            parents[node_id] = parent
    edges = []
    invalid_links = 0
    for node_id, parent in parents.items():
        if parent == -1:
            continue
        if parent not in nodes:
            warnings.append(f'node {node_id}: missing parent {parent}; segment omitted')
            invalid_links += 1
        else:
            edges.append((node_id, parent))
    return {'nodes': nodes, 'edges': edges, 'metadata': metadata,
            'skipped_rows': skipped, 'invalid_links': invalid_links, 'warnings': warnings}


def load_skeletons(directory, selected):
    skeletons, errors = {}, {}
    for root_id in selected:
        try:
            skeleton = load_skeleton(Path(directory) / f'{root_id}.swc', root_id)
            skeletons[root_id] = skeleton
            if not skeleton['nodes']:
                errors[root_id] = 'no valid SWC nodes'
        except (OSError, UnicodeError, ValueError) as exc:
            errors[root_id] = str(exc)
    return skeletons, errors


def validate_morphology(directory=SKELETON_DIR, selected=None):
    """Print and return selected-file counts without opening a window."""
    selected = SELECTED_NEURONS if selected is None else selected
    skeletons, errors = load_skeletons(directory, selected)
    found = sum((Path(directory) / f'{rid}.swc').is_file() for rid in selected)
    print(f'SWC files found: {found}/{len(selected)} selected')
    for rid, label in selected.items():
        skeleton = skeletons.get(rid)
        if skeleton is not None:
            print(f'{label} ({rid}): nodes={len(skeleton["nodes"])}, '
                  f'segments={len(skeleton["edges"])}, skipped rows={skeleton["skipped_rows"]}, '
                  f'invalid links={skeleton["invalid_links"]}')
            for warning in skeleton['warnings'][:10]:
                print(f'  {warning}')
            if len(skeleton['warnings']) > 10:
                print('  Further warnings available in returned skeleton data.')
        if rid in errors:
            print(f'{label} ({rid}): {errors[rid]}')
    return {'found': found, 'skeletons': skeletons, 'errors': errors}


def project(point, yaw, pitch, scale, center):
    """Orthographic projection after yaw and pitch rotations."""
    x, y, z = point
    x, z = math.cos(yaw) * x + math.sin(yaw) * z, -math.sin(yaw) * x + math.cos(yaw) * z
    y, z = math.cos(pitch) * y - math.sin(pitch) * z, math.sin(pitch) * y + math.cos(pitch) * z
    return (round(center[0] + x * scale), round(center[1] - y * scale))


class NeuralVisualizer:
    """One-way bounded snapshots: a slow/closed viewer never blocks simulation."""
    def __init__(self, directory=SKELETON_DIR, selected=None):
        self.selected = dict(SELECTED_NEURONS if selected is None else selected)
        context = mp.get_context('spawn')
        self.snapshots = context.Queue(maxsize=1)
        self.stop = context.Event()
        self.process = context.Process(target=_viewer, args=(str(directory), self.selected,
                                                            self.snapshots, self.stop), daemon=True)
        self.last_publish = -float('inf')
        self.process.start()

    def publish(self, activations):
        now = time.monotonic()
        if not self.process.is_alive() or now - self.last_publish < 1 / 20:
            return
        # Copy only selected scalar values; no graph/state object crosses processes.
        snapshot = {root_id: float(activations[root_id]) for root_id in self.selected
                    if root_id in activations}
        try:
            self.snapshots.put_nowait(snapshot)
            self.last_publish = now
        except queue.Full:
            pass

    def close(self):
        self.stop.set()
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
        self.snapshots.cancel_join_thread()
        self.snapshots.close()


def _viewer(directory, selected, snapshots, stop):
    import pygame
    skeletons, errors = load_skeletons(directory, selected)
    context_mesh, context_status = load_context(Path(directory) / "context")
    print(context_status, flush=True)
    for root_id, error in errors.items():
        print(f'Skeleton {root_id}: {error}', flush=True)
    # Use a single shared origin/scale, preserving inter-neuron spatial geometry.
    points = [p for s in skeletons.values() for p in s['nodes'].values()]
    midpoint, extent = (0, 0, 0), 1
    if points:
        low = [min(p[i] for p in points) for i in range(3)]
        high = [max(p[i] for p in points) for i in range(3)]
        midpoint = tuple((a + b) / 2 for a, b in zip(low, high))
        extent = max(max(b - a for a, b in zip(low, high)), 1)
    normalized = {rid: {nid: tuple((p[i] - midpoint[i]) / extent for i in range(3))
                        for nid, p in s['nodes'].items()} for rid, s in skeletons.items()}
    # Context uses the skeleton transform, never independent normalization.
    context_points = ([] if context_mesh is None else
                      [tuple((p[i] - midpoint[i]) / extent for i in range(3))
                       for p in context_mesh['vertices']])
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1100, 750), pygame.RESIZABLE)
    pygame.display.set_caption('NeuroFly — read-only FlyWire skeletons')
    font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()
    yaw, pitch, zoom = 0.0, 0.0, 1.0
    activities = {}
    show_context, show_labels = True, True
    try:
        while not stop.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    yaw += event.rel[0] * 0.008
                    pitch += event.rel[1] * 0.008
                if event.type == pygame.MOUSEWHEEL:
                    zoom = max(0.1, min(20, zoom * 1.12 ** event.y))
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    yaw, pitch, zoom = 0.0, 0.0, 1.0
                if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                    show_context = not show_context
                if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                    show_labels = not show_labels
            try:
                activities = snapshots.get_nowait()
            except queue.Empty:
                pass
            screen.fill((15, 18, 25))
            width, height = screen.get_size()
            scale = min(width, height) * 0.65 * zoom
            center = (width * 0.58, height * 0.62)
            if show_context and context_mesh is not None:
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                projected_context = [project(p, yaw, pitch, scale, center) for p in context_points]
                for a, b in context_mesh['edges']:
                    pygame.draw.line(overlay, CONTEXT_COLOR, projected_context[a], projected_context[b], 1)
                screen.blit(overlay, (0, 0))
            # Draw neurons last so context never obscures activation colors.
            for index, (rid, label) in enumerate(selected.items()):
                value = activities.get(rid, 0.0)
                value = max(0.0, min(1.0, value)) if math.isfinite(value) else 0.0
                color = tuple(round(c * (0.2 + 0.8 * value)) for c in COLORS[index % len(COLORS)])
                if rid in skeletons:
                    projected = {nid: project(p, yaw, pitch, scale, center)
                                 for nid, p in normalized[rid].items()}
                    for a, b in skeletons[rid]['edges']:
                        pygame.draw.line(screen, color, projected[a], projected[b], 1 + round(2 * value))
                status = ('missing/invalid morphology' if rid in errors else
                          f"loaded ({len(skeletons[rid]['warnings'])} warnings)")
                activity_label = f'{value:.3f}' if rid in activities else 'no live sample'
                text = f'{label}: {activity_label} — {status}'
                if show_labels:
                    screen.blit(font.render(text, True, COLORS[index % len(COLORS)]), (12, 45 + index * 23))
            screen.blit(font.render('Drag: rotate | Wheel: zoom | R: reset | B: context | L: labels | Close: simulation continues',
                                    True, (240, 240, 240)), (12, 12))
            context_label = context_status if show_context else 'Brain context hidden (B)'
            screen.blit(font.render(context_label, True, (150, 150, 150)), (12, height - 65))
            if not skeletons:
                screen.blit(font.render('No morphology loaded. See brain/visualization_3d.md; no coordinates invented.',
                                        True, (240, 200, 130)), (12, height - 40))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.quit()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Inspect local skeletons without a simulation.')
    parser.add_argument('--skeleton-dir', type=Path, default=SKELETON_DIR)
    parser.add_argument('--validate', action='store_true', help='Report SWC counts without a window')
    args = parser.parse_args()
    if args.validate:
        validate_morphology(args.skeleton_dir)
    else:
        context = mp.get_context('spawn')
        _viewer(str(args.skeleton_dir), SELECTED_NEURONS, context.Queue(1), context.Event())

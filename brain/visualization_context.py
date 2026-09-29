"""Optional read-only OBJ wireframe context; no generated fallback anatomy."""
import math
from pathlib import Path

CONTEXT_FILENAME = 'brain.obj'
CONTEXT_COLOR = (160, 160, 160, 40)


def load_context(directory):
    """Return (mesh, status). Invalid files are disabled, never partly invented."""
    path = Path(directory) / CONTEXT_FILENAME
    if not path.is_file():
        return None, 'Brain context unavailable (no brain.obj)'
    vertices, edges = [], set()
    try:
        with path.open(encoding='utf-8-sig') as stream:
            for line_number, line in enumerate(stream, 1):
                fields = line.split('#', 1)[0].split()
                if not fields:
                    continue
                if fields[0] == 'v':
                    if len(fields) != 4:
                        raise ValueError('vertices require exactly x y z')
                    point = tuple(float(v) for v in fields[1:])
                    if not all(math.isfinite(v) for v in point):
                        raise ValueError('nonfinite vertex')
                    vertices.append(point)
                elif fields[0] in ('f', 'l'):
                    indices = []
                    for token in fields[1:]:
                        index = int(token.split('/')[0])
                        if index == 0:
                            raise ValueError('OBJ indices cannot be zero')
                        index = index - 1 if index > 0 else len(vertices) + index
                        if not 0 <= index < len(vertices):
                            raise ValueError('vertex index is missing or not yet declared')
                        indices.append(index)
                    if len(indices) < (3 if fields[0] == 'f' else 2):
                        raise ValueError('not enough face/line vertices')
                    pairs = list(zip(indices, indices[1:]))
                    if fields[0] == 'f':
                        pairs.append((indices[-1], indices[0]))
                    for a, b in pairs:
                        if a != b:
                            edges.add(tuple(sorted((a, b))))
        if not vertices or not edges:
            raise ValueError('mesh needs vertices and faces or lines')
        return {'vertices': vertices, 'edges': sorted(edges)}, 'Brain context loaded'
    except (OSError, UnicodeError, ValueError) as exc:
        return None, f'Brain context disabled: {path.name}: {exc}'

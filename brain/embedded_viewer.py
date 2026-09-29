"""Off-screen renderer bridge. Only pixels return to the main application."""
import multiprocessing as mp
import queue
import time

from brain.visualization_3d import SELECTED_NEURONS, SKELETON_DIR, _viewer


def _render_worker(directory, selected, snapshots, stop, offscreen, errors):
    try:
        _viewer(directory, selected, snapshots, stop, offscreen)
    except Exception as exc:
        try:
            errors.put_nowait(f'{type(exc).__name__}: {exc}')
        except queue.Full:
            pass


class EmbeddedBrainViewer:
    def __init__(self, size, directory=SKELETON_DIR, selected=None):
        self.size = tuple(size)
        self.selected = dict(SELECTED_NEURONS if selected is None else selected)
        self.camera = [0.0, 0.0, 1.0, True, True]
        self.surface = None
        self.status = 'Loading brain morphology…'
        self.failed = False
        self.last_publish = -float('inf')
        context = mp.get_context('spawn')
        self.snapshots = context.Queue(1)
        self.errors = context.Queue(1)
        self.stop = context.Event()
        self.frame_ready = context.Event()
        self.frame_lock = context.Lock()
        self.pixels = context.RawArray('B', size[0] * size[1] * 3)
        self.process = context.Process(target=_render_worker, args=(
            str(directory), self.selected, self.snapshots, self.stop,
            (self.size, self.pixels, self.frame_lock, self.frame_ready), self.errors), daemon=True)
        try:
            self.process.start()
        except Exception:
            self.snapshots.close()
            self.errors.close()
            raise

    def handle_event(self, event, panel, mouse_position):
        import pygame
        if not panel.collidepoint(getattr(event, 'pos', mouse_position)):
            return
        if event.type == pygame.MOUSEMOTION and event.buttons[0]:
            self.camera[0] += event.rel[0] * 0.008
            self.camera[1] += event.rel[1] * 0.008
        elif event.type == pygame.MOUSEWHEEL:
            self.camera[2] = max(0.1, min(20, self.camera[2] * 1.12 ** event.y))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.camera[:3] = [0.0, 0.0, 1.0]
            elif event.key == pygame.K_b:
                self.camera[3] = not self.camera[3]
            elif event.key == pygame.K_l:
                self.camera[4] = not self.camera[4]

    def publish(self, activations):
        if self.failed or not self.process.is_alive():
            return
        now = time.monotonic()
        if now - self.last_publish < 1 / 25:
            return
        packet = ({rid: float(activations[rid]) for rid in self.selected if rid in activations},
                  tuple(self.camera))
        try:
            self.snapshots.put_nowait(packet)
            self.last_publish = now
        except queue.Full:
            pass

    def poll(self):
        """Never wait for a renderer/frame lock. Retain the last complete surface."""
        import pygame
        if self.failed:
            return self.surface
        try:
            error = self.errors.get_nowait()
        except queue.Empty:
            error = None
        if error or not self.process.is_alive():
            self.failed = True
            self.status = 'Brain renderer unavailable; simulation continues.'
            if error:
                print(f'{self.status} {error}', flush=True)
            return self.surface
        if self.frame_ready.is_set() and self.frame_lock.acquire(False):
            try:
                frame = bytes(self.pixels)
                self.frame_ready.clear()
            finally:
                self.frame_lock.release()
            try:
                self.surface = pygame.image.frombytes(frame, self.size, 'RGB')
                self.status = ''
            except Exception as exc:
                self.failed = True
                self.status = f'Brain frame unavailable: {exc}'
                self.stop.set()
        return self.surface

    def close(self):
        self.stop.set()
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
        for channel in (self.snapshots, self.errors):
            channel.cancel_join_thread()
            channel.close()

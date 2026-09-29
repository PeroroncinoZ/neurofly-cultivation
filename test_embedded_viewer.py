"""Headless integration tests for the off-screen worker and application fallback."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import tempfile
import time
from pathlib import Path
import unittest
from unittest.mock import patch

import pygame
from brain.embedded_viewer import EmbeddedBrainViewer


class EmbeddedViewerTests(unittest.TestCase):
    def test_worker_frame_controls_read_only_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '1.swc'
            data = '1 1 0 0 0 1 -1\n2 3 1 1 1 1 1\n'
            path.write_text(data)
            viewer = EmbeddedBrainViewer((320, 240), directory, {1: 'Test neuron'})
            try:
                activation = {1: 0.5}
                viewer.publish(activation)
                deadline = time.monotonic() + 10
                while viewer.surface is None and time.monotonic() < deadline:
                    viewer.poll()
                    time.sleep(0.01)
                self.assertIsNotNone(viewer.surface)
                self.assertEqual(viewer.surface.get_size(), (320, 240))
                self.assertEqual(activation, {1: 0.5})
                self.assertEqual(path.read_text(), data)
                panel = pygame.Rect(800, 0, 320, 240)
                toggle = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
                viewer.handle_event(toggle, panel, (100, 100))
                self.assertTrue(viewer.camera[3])
                viewer.handle_event(toggle, panel, (900, 100))
                self.assertFalse(viewer.camera[3])
                viewer.handle_event(pygame.event.Event(pygame.MOUSEMOTION,
                    pos=(900, 100), rel=(10, 5), buttons=(1, 0, 0)), panel, (900, 100))
                self.assertNotEqual(viewer.camera[0], 0)
                viewer.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1), panel, (900, 100))
                self.assertGreater(viewer.camera[2], 1)
                viewer.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r), panel, (900, 100))
                self.assertEqual(viewer.camera[:3], [0, 0, 1])
                viewer.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_l), panel, (900, 100))
                self.assertFalse(viewer.camera[4])
                viewer.process.terminate()
                viewer.process.join(timeout=2)
                viewer.poll()
                self.assertTrue(viewer.failed)
                self.assertIn('simulation continues', viewer.status)
            finally:
                viewer.close()

    def test_main_startup_failure_preserves_arena_and_capture(self):
        import main
        from fly import Fly
        from spiritual_fruit import SpiritualFruit
        flies = []
        def make_fly(*args):
            fly = Fly(*args)
            flies.append(fly)
            return fly
        with patch('brain.embedded_viewer.EmbeddedBrainViewer', side_effect=RuntimeError('test failure')), \
             patch('main.Fly', side_effect=make_fly), \
             patch('main.movement_touches_fruit', return_value=True), \
             patch('main.spawn_fruit', return_value=SpiritualFruit(600, 200)) as spawn, \
             patch('pygame.event.get', side_effect=[[], [], [pygame.event.Event(pygame.QUIT)]]):
            main.main()
        self.assertEqual(flies[0].qi, 2)
        spawn.assert_called_with(800, 600)

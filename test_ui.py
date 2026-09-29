import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from ui import SimulatorUI, WORLD_RECT, BRAIN_RECT


class UITests(unittest.TestCase):
    def test_modes_and_fixed_arena(self):
        pygame.font.init()
        ui = SimulatorUI()
        self.assertFalse(ui.debug)
        ui.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
        self.assertTrue(ui.debug)
        ui.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
        self.assertFalse(ui.debug)
        self.assertEqual(WORLD_RECT.size, (800, 600))
        self.assertFalse(WORLD_RECT.colliderect(BRAIN_RECT))

    def test_both_modes_in_application(self):
        import main
        with patch('pygame.event.get', side_effect=[[],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)],
            [pygame.event.Event(pygame.QUIT)]]):
            main.main(visualize_3d=False)

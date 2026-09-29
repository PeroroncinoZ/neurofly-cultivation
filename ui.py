"""Read-only presentation/layout for NeuroFly; no simulation decisions."""
import math
import pygame
from brain.visualization_3d import SELECTED_NEURONS, COLORS

WINDOW_SIZE = (1648, 960)
ARENA_SIZE = (800, 600)
WORLD_RECT = pygame.Rect(16, 88, 800, 600)
BRAIN_RECT = pygame.Rect(832, 88, 800, 600)
BACKGROUND = (14, 18, 25)
PANEL = (22, 28, 37)
TEXT = (220, 228, 237)
MUTED = (142, 156, 174)


class SimulatorUI:
    def __init__(self):
        self.debug = False
        self.font = pygame.font.Font(None, 23)
        self.small = pygame.font.Font(None, 20)
        self.title = pygame.font.Font(None, 34)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.debug = False
            elif event.key == pygame.K_d:
                self.debug = not self.debug

    def text(self, screen, value, position, color=TEXT, font=None):
        screen.blit((font or self.font).render(value, True, color), position)

    def begin(self, screen):
        screen.fill(BACKGROUND)
        pygame.draw.rect(screen, (30, 30, 30), WORLD_RECT)
        pygame.draw.rect(screen, (15, 18, 25), BRAIN_RECT)
        self.text(screen, 'NeuroFly: Cultivation', (16, 18), font=self.title)
        self.text(screen, 'D  Debug   /   P  Presentation', (1320, 26), MUTED, self.small)
        self.text(screen, 'Cultivation World', (16, 62))
        self.text(screen, 'FlyWire Neural Activity', (832, 62))
        for rect in (WORLD_RECT, BRAIN_RECT):
            pygame.draw.rect(screen, (48, 59, 73), rect.inflate(2, 2), 1)

    def draw(self, screen, cultivation, controller, fly, boundary, neural, turn_rate,
             viewer_status='', show_labels=True, message=''):
        # Values are observed only; input objects are never mutated.
        if show_labels:
            for index, (_, label) in enumerate(SELECTED_NEURONS.items()):
                x = 840 + (index % 4) * 196
                y = 700 + (index // 4) * 21
                pygame.draw.circle(screen, COLORS[index], (x + 4, y + 6), 3)
                self.text(screen, label, (x + 15, y), MUTED, self.small)
        self.text(screen, 'Brain controls (hover): drag / wheel   R reset   B context   L labels',
                  (840, 746), MUTED, self.small)
        if viewer_status:
            # Status belongs outside the scene, clipped to its dedicated strip.
            old_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(16, 723, 800, 24))
            self.text(screen, viewer_status, (16, 725), MUTED, self.small)
            screen.set_clip(old_clip)
        if message:
            self.text(screen, message, (16, 700), (206, 192, 144), self.small)
        pygame.draw.rect(screen, PANEL, (16, 777, 1616, 38), border_radius=4)
        requirement = cultivation.next_stage_qi
        qi = f'{fly.qi}/{requirement}' if requirement is not None else f'{fly.qi} (Max stage)'
        status = (f'Stage: {cultivation.stage}   |   Qi: {qi}   |   Mode: {controller.mode}'
                  f'   |   Odor: {controller.total_odor:.2f}'
                  f'   |   DNa02 L-R: {controller.motor_decoder.steering_difference:+.4f}')
        self.text(screen, status, (28, 788))
        if not self.debug:
            self.text(screen, 'Presentation mode  •  Press D for detailed neural metrics',
                      (16, 837), MUTED, self.small)
            return
        decoder = controller.motor_decoder
        columns = [
            ['SENSORY INPUT',
             f"Odor L/R: {neural['left_odor_input']:.3f} / {neural['right_odor_input']:.3f}",
             f"ORN L/R: {neural['left_orn_average']:.3f} / {neural['right_orn_average']:.3f}",
             f'Odor change: {controller.smoothed_odor_change:+.3f}/s',
             f'Alignment threshold: {controller.alignment_threshold:.4f}'],
            ['FLYWIRE PATHWAY',
             f"DM1 L/R: {neural['dm1_lpn_left']:.3f} / {neural['dm1_lpn_right']:.3f}",
             f"APL L/R: {neural['apl_left']:.3f} / {neural['apl_right']:.3f}",
             f"MBON32 L/R: {neural['mbon32_left']:.3f} / {neural['mbon32_right']:.3f}",
             f"DNa02 L/R: {neural['dna02_left']:.4f} / {neural['dna02_right']:.4f}"],
            ['MOTOR OUTPUT',
             f'Smoothed DNa02: {decoder.smoothed_difference:+.5f}',
             f'Applied gain: {decoder.applied_gain:.1f}',
             f'Turn rate: {turn_rate:+.3f} rad/s',
             f'Speed: {fly.applied_speed:.1f} px/s'],
            ['BODY / ARENA',
             f'Heading: {math.degrees(fly.heading):.1f} deg',
             f'Position: ({fly.x:.2f}, {fly.y:.2f})',
             f'Boundary active: {boundary.active}',
             f'Controller: {controller.mode}'],
        ]
        for col, lines in enumerate(columns):
            rect = pygame.Rect(16 + col * 408, 827, 392, 120)
            pygame.draw.rect(screen, PANEL, rect, border_radius=4)
            for row, line in enumerate(lines):
                self.text(screen, line, (rect.x + 12, rect.y + 10 + row * 21),
                          MUTED if row == 0 else TEXT, self.small)

import math
import random

import pygame

from brain.brain_interface import BrainInterface
from controller import Controller
from cultivation import Cultivation
from ui import SimulatorUI, WINDOW_SIZE, ARENA_SIZE, WORLD_RECT, BRAIN_RECT
from boundary import BoundaryAvoidance
from collision import movement_touches_fruit
from fly import Fly
from senses import sense_fruit
from spiritual_fruit import (SpiritualFruit, SPAWN_MARGIN, create_random_fruit,
                             CONSUMPTION_MESSAGE_SECONDS)


def spawn_fruit(width, height, margin=SPAWN_MARGIN):
    fruit = create_random_fruit(0, 0)
    inset = math.ceil(max(fruit.radius, margin))
    if width < 2 * inset or height < 2 * inset:
        raise ValueError("window is too small for the fruit spawn margin")
    fruit.x = random.randint(inset, width - inset)
    fruit.y = random.randint(inset, height - inset)
    return fruit


def main(visualize_3d=True, skeleton_dir=None):
    brain = BrainInterface()
    pygame.init()
    arena_size = ARENA_SIZE
    screen = pygame.display.set_mode(WINDOW_SIZE)
    arena = screen.subsurface(WORLD_RECT)
    brain_panel = BRAIN_RECT
    pygame.display.set_caption("NeuroFly: Cultivation")
    clock = pygame.time.Clock()
    ui = SimulatorUI()
    fly = Fly(400, 300)
    controller = Controller()
    cultivation = Cultivation()
    boundary = BoundaryAvoidance()
    fruit = SpiritualFruit(600, 200)

    visualizer = None
    viewer_status = 'Brain panel disabled (--no-brain).'
    if visualize_3d:
        try:
            from brain.embedded_viewer import EmbeddedBrainViewer
            from brain.visualization_3d import SKELETON_DIR
            visualizer = EmbeddedBrainViewer(brain_panel.size,
                SKELETON_DIR if skeleton_dir is None else skeleton_dir)
        except Exception as exc:
            viewer_status = f'Brain renderer unavailable: {exc}'
            print(viewer_status, flush=True)

    consumption_message = ""
    message_until = 0.0
    simulation_time = 0.0
    running = True
    try:
        while running:
            elapsed = clock.tick(60) / 1000.0
            simulation_time += elapsed
            for event in pygame.event.get():
                ui.handle_event(event)
                if visualizer is not None:
                    visualizer.handle_event(event, brain_panel, pygame.mouse.get_pos())
                if event.type == pygame.QUIT:
                    running = False

            if not running:
                break

            senses = sense_fruit(fly, fruit)
            brain.update(senses["left_odor"], senses["right_odor"])
            if visualizer is not None:
                visualizer.publish(brain.state["activations"])
            brain_debug = brain.get_debug_values()
            turn_rate = controller.choose_turn_rate(
                brain_debug["odor_input"], brain_debug["dna02_left"],
                brain_debug["dna02_right"], simulation_time,
            )
            turn_rate = boundary.apply(fly, *arena_size,
                                       turn_rate, elapsed, controller.total_odor,
                                       fly.speed * controller.speed_scale)
            start = (fly.x, fly.y)
            fly.move(turn_rate, elapsed, controller.speed_scale * boundary.speed_scale)
            fly.keep_inside(*arena_size)
            captured = movement_touches_fruit(start, (fly.x, fly.y), fly.radius, fruit)

            if captured:
                fly.qi += fruit.qi_value
                consumption_message = fruit.consumption_message()
                message_until = simulation_time + CONSUMPTION_MESSAGE_SECONDS
                # Replacing the old fruit removes it from the world.
                fruit = spawn_fruit(*arena_size)

            cultivation.update(fly.qi)

            # Clear the previous frame before drawing the fruit and fly again.
            ui.begin(screen)
            fruit.draw(arena)
            fly.draw(arena)
            pygame.draw.rect(screen, (15, 18, 25), brain_panel)
            if visualizer is not None:
                frame = visualizer.poll()
                if frame is not None:
                    screen.blit(frame, brain_panel.topleft)
                viewer_status = visualizer.status
            ui.draw(screen, cultivation, controller, fly, boundary, brain_debug, turn_rate,
                    viewer_status=viewer_status,
                    show_labels=visualizer.camera[4] if visualizer is not None else True,
                    message=consumption_message if simulation_time < message_until else '')
            pygame.display.flip()

    finally:
        if visualizer is not None:
            visualizer.close()
        pygame.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--visualize-3d', action='store_true', help='Legacy alias; brain panel is enabled by default')
    parser.add_argument('--no-brain', action='store_true', help='Disable the embedded renderer')
    parser.add_argument('--skeleton-dir', default=None)
    args = parser.parse_args()
    main(visualize_3d=not args.no_brain, skeleton_dir=args.skeleton_dir)

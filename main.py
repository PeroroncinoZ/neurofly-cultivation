import math
import random

import pygame

from brain.brain_interface import BrainInterface
from controller import Controller
from fly import Fly
from senses import sense_fruit
from spiritual_fruit import SpiritualFruit


def circles_touch(first, second):
    distance = math.hypot(first.x - second.x, first.y - second.y)
    return distance <= first.radius + second.radius


def spawn_fruit(width, height):
    fruit = SpiritualFruit(0, 0)
    # Keep the whole fruit inside the window.
    fruit.x = random.randint(fruit.radius, width - fruit.radius)
    fruit.y = random.randint(fruit.radius, height - fruit.radius)
    return fruit


def main():
    brain = BrainInterface()
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("NeuroFly: Cultivation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    fly = Fly(400, 300)
    controller = Controller()
    fruit = SpiritualFruit(600, 200)

    simulation_time = 0.0
    running = True
    while running:
        elapsed = clock.tick(60) / 1000.0
        simulation_time += elapsed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running:
            break

        senses = sense_fruit(fly, fruit)
        brain.update(senses["left_odor"], senses["right_odor"])
        brain_debug = brain.get_debug_values()
        turn_rate = controller.choose_turn_rate(
            brain_debug["odor_input"], brain_debug["dna02_left"],
            brain_debug["dna02_right"], simulation_time,
        )
        fly.move(turn_rate, elapsed)
        fly.keep_inside(screen.get_width(), screen.get_height())

        if circles_touch(fly, fruit):
            fly.qi += 1
            # Replacing the old fruit removes it from the world.
            fruit = spawn_fruit(screen.get_width(), screen.get_height())

        # Clear the previous frame before drawing the fruit and fly again.
        screen.fill((30, 30, 30))
        fruit.draw(screen)
        fly.draw(screen)
        debug_lines = [
            f"Qi: {fly.qi}",
            f"Mode: {controller.mode}",
            f"Heading: {math.degrees(fly.heading):.1f} deg",
            f"Left odor input: {brain_debug['left_odor_input']:.3f}",
            f"Right odor input: {brain_debug['right_odor_input']:.3f}",
            f"ORN mean L/R: {brain_debug['left_orn_average']:.3f} / {brain_debug['right_orn_average']:.3f}",
            f"DM1_lPN L/R: {brain_debug['dm1_lpn_left']:.3f} / {brain_debug['dm1_lpn_right']:.3f}",
            f"APL L/R: {brain_debug['apl_left']:.3f} / {brain_debug['apl_right']:.3f}",
            f"MBON32 L/R: {brain_debug['mbon32_left']:.3f} / {brain_debug['mbon32_right']:.3f}",
            f"DNa02 left: {brain_debug['dna02_left']:.4f}",
            f"DNa02 right: {brain_debug['dna02_right']:.4f}",
            f"Raw DNa02 difference (R - L): {brain_debug['dna02_difference']:+.4f}",
            f"Applied turn rate: {turn_rate:+.3f} rad/s",
            f"Forward speed: {fly.speed:.1f} px/s",
            f"Position: ({fly.x:.3f}, {fly.y:.3f})",
        ]
        for index, line in enumerate(debug_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + index * 28))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

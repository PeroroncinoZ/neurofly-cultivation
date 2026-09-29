"""Deterministic near-wall trials; run directly for consumption/containment reports."""
import math
import random
import unittest

from boundary import BoundaryAvoidance
from brain.brain_interface import BrainInterface
from collision import movement_touches_fruit
from controller import Controller
from fly import Fly
from main import spawn_fruit
from senses import sense_fruit
from spiritual_fruit import SpiritualFruit, SPAWN_MARGIN


def run_trial(position, start, heading):
    fruit = SpiritualFruit(*position)
    fly = Fly(*start, heading=heading)
    brain, controller, boundary = BrainInterface(), Controller(rng=random.Random(42)), BoundaryAvoidance()
    state = random.getstate()
    random.seed(42)
    consumed, inside = False, True
    try:
        for frame in range(600):
            odor = sense_fruit(fly, fruit)
            brain.update(odor['left_odor'], odor['right_odor'])
            activity = brain.get_debug_values()
            turn = controller.choose_turn_rate(activity['odor_input'], activity['dna02_left'],
                                              activity['dna02_right'], frame / 60)
            turn = boundary.apply(fly, 800, 600, turn, 1 / 60, controller.total_odor,
                                  fly.speed * controller.speed_scale)
            start = (fly.x, fly.y)
            fly.move(turn, 1 / 60, controller.speed_scale)
            fly.keep_inside(800, 600)
            inside &= 10 <= fly.x <= 790 and 10 <= fly.y <= 590
            consumed = movement_touches_fruit(start, (fly.x, fly.y), fly.radius, fruit)
            if consumed:
                break
    finally:
        random.setstate(state)
    return consumed, inside


TRIALS = {
    'left wall': ((45, 300), (120, 300), math.pi),
    'right wall': ((755, 300), (680, 300), 0),
    'corner': ((45, 45), (100, 100), -3 * math.pi / 4),
}


class CaptureBoundaryTests(unittest.TestCase):
    def test_near_wall_trials(self):
        for name, args in TRIALS.items():
            with self.subTest(name=name):
                self.assertEqual(run_trial(*args), (True, True))

    def test_between_frame_capture_and_miss(self):
        fruit = SpiritualFruit(400, 300)
        self.assertTrue(movement_touches_fruit((300, 330), (500, 330), 10, fruit))
        self.assertFalse(movement_touches_fruit((300, 336), (500, 336), 10, fruit))
        self.assertTrue(movement_touches_fruit((400, 335), (400, 335), 10, fruit))

    def test_high_odor_slow_motion_softens_wall_turn(self):
        fly = Fly(770, 300)
        normal = BoundaryAvoidance().apply(fly, 800, 600, 0, 0.1, 0.2, 30)
        softened = BoundaryAvoidance().apply(fly, 800, 600, 0, 0.1, 0.95, 30)
        self.assertTrue(0 < softened < normal)
        fly.heading = math.pi
        avoidance = BoundaryAvoidance()
        self.assertEqual(avoidance.apply(fly, 800, 600, 0.2, 0.1), 0.2)
        self.assertFalse(avoidance.active)

    def test_spawn_margin(self):
        for _ in range(100):
            fruit = spawn_fruit(800, 600)
            self.assertTrue(SPAWN_MARGIN <= fruit.x <= 800 - SPAWN_MARGIN)
            self.assertTrue(SPAWN_MARGIN <= fruit.y <= 600 - SPAWN_MARGIN)


if __name__ == '__main__':
    for name, args in TRIALS.items():
        consumed, inside = run_trial(*args)
        print(f'{name}: consumed={consumed}, stayed inside={inside}')
    fly = Fly(300, 330, speed=1200)
    start = (fly.x, fly.y)
    fly.move(0, 1 / 6)
    fly.keep_inside(800, 600)
    print('between frames: consumed=' + str(movement_touches_fruit(
        start, (fly.x, fly.y), fly.radius, SpiritualFruit(400, 300)))
        + f', stayed inside={10 <= fly.x <= 790 and 10 <= fly.y <= 590}')

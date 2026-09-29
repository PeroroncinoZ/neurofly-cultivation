"""Run deterministic steering diagnostics: python test_neural_steering.py.

Each trial runs for 10 seconds at 60 Hz with a fresh neural state. Sensor noise
is preserved and seeded; search randomness uses a separate seeded generator.
Fruit stays fixed for the entire trial, even after contact. Success means the
fly touched the fruit at least once, not necessarily at the final frame.
Fruit-relative distance and heading error are evaluation metrics only.
"""

import math
import random

from brain.brain_interface import BrainInterface
from controller import Controller
from boundary import BoundaryAvoidance
from collision import movement_touches_fruit
from fly import Fly
from senses import sense_fruit
from spiritual_fruit import SpiritualFruit


WINDOW_SIZE = (800, 600)
START_POSITION = (400, 300)
INITIAL_HEADING = -math.pi / 2  # Facing screen-up in every trial.
SECONDS = 10
FPS = 60
SEED = 42
SCENARIOS = {
    "left": (200, 300),
    "right": (600, 300),
    "upper-left": (250, 150),
    "upper-right": (550, 150),
}


def evaluation_metrics(fly, fruit):
    """Distance in pixels and absolute shortest heading error in degrees."""
    offset_x, offset_y = fruit.x - fly.x, fruit.y - fly.y
    distance = math.hypot(offset_x, offset_y)
    if distance == 0:
        return distance, 0.0  # Bearing is undefined at the fruit center.
    bearing = math.atan2(offset_y, offset_x)
    error = (bearing - fly.heading + math.pi) % math.tau - math.pi
    return distance, abs(math.degrees(error))


def run_scenario(name, fruit_position):
    fly = Fly(*START_POSITION, heading=INITIAL_HEADING)
    fruit = SpiritualFruit(*fruit_position)
    brain = BrainInterface()
    controller = Controller(rng=random.Random(SEED))
    boundary = BoundaryAvoidance()
    start_distance, start_error = evaluation_metrics(fly, fruit)
    totals = dict.fromkeys(
        ("left_odor_input", "right_odor_input", "dna02_left", "dna02_right"), 0.0
    )
    reached = False
    following_frames = 0
    boundary_frames = 0
    steps = SECONDS * FPS

    # The existing sensors use the global RNG. Seed it without altering their
    # noise distribution, and restore it so callers' random state is unaffected.
    random_state = random.getstate()
    random.seed(SEED)
    try:
        for step in range(steps):
            odor = sense_fruit(fly, fruit)
            brain.update(odor["left_odor"], odor["right_odor"])
            activity = brain.get_debug_values()
            turn_rate = controller.choose_turn_rate(
                activity["odor_input"], activity["dna02_left"],
                activity["dna02_right"], (step + 1) / FPS,
            )
            # Only neural activity and scalar odor detection enter the controller.
            # Its existing detected-odor branch never samples random search turns.
            following_frames += controller.mode == "NEURAL FOLLOWING"
            for key in totals:
                totals[key] += activity[key]
            turn_rate = boundary.apply(fly, *WINDOW_SIZE, turn_rate, 1 / FPS)
            start = (fly.x, fly.y)
            fly.move(turn_rate, 1 / FPS, controller.speed_scale)
            boundary_frames += any(fly.keep_inside(*WINDOW_SIZE))
            reached |= movement_touches_fruit(start, (fly.x, fly.y), fly.radius, fruit)
    finally:
        random.setstate(random_state)

    end_distance, end_error = evaluation_metrics(fly, fruit)
    return {
        "scenario": name,
        "starting_distance": start_distance,
        "ending_distance": end_distance,
        "starting_heading_error": start_error,
        "ending_heading_error": end_error,
        **{f"mean_{key}": value / steps for key, value in totals.items()},
        "reached_fruit": reached,
        "following_seconds": following_frames / FPS,
        "boundary_frames": boundary_frames,
    }


def main():
    print(f"Neural steering: {SECONDS}s/trial, {FPS} Hz, seed {SEED}")
    print(f"Start {START_POSITION}, heading {math.degrees(INITIAL_HEADING):.0f} deg; "
          f"window {WINDOW_SIZE}; odor-dependent speed; default sensor noise preserved.")
    print("Heading errors are absolute (0 deg = facing fruit). "
          "Means cover the full trial; success = any fruit contact.")
    results = []
    for name, position in SCENARIOS.items():
        result = run_scenario(name, position)
        results.append(result)
        print(f"\n{name} — fruit {position}: "
              f"reached={'YES' if result['reached_fruit'] else 'NO'}")
        print(f"  Distance: {result['starting_distance']:.2f} -> "
              f"{result['ending_distance']:.2f} px; heading error: "
              f"{result['starting_heading_error']:.2f} -> "
              f"{result['ending_heading_error']:.2f} deg")
        print(f"  Mean odor L/R: {result['mean_left_odor_input']:.5f} / "
              f"{result['mean_right_odor_input']:.5f}; mean DNa02 L/R: "
              f"{result['mean_dna02_left']:.5f} / {result['mean_dna02_right']:.5f}")
        print(f"  Neural following: {result['following_seconds']:.2f}s; "
              f"wall-contact frames: {result['boundary_frames']}")
    successes = sum(result["reached_fruit"] for result in results)
    print(f"\nOverall success: {successes}/{len(results)} reached the fruit.")


if __name__ == "__main__":
    main()

import math
import random
from dataclasses import dataclass
from enum import Enum

import pygame

CAPTURE_RADIUS = 35.0
SPAWN_BUFFER = 10.0
SPAWN_MARGIN = CAPTURE_RADIUS + SPAWN_BUFFER


class FruitType(str, Enum):
    COMMON = 'COMMON'
    RARE = 'RARE'
    TOXIC = 'TOXIC'


@dataclass(frozen=True)
class FruitData:
    name: str
    qi_value: int
    spawn_weight: float
    color: tuple


FRUIT_TYPES = {
    FruitType.COMMON: FruitData('Common Spirit Fruit', 1, 70, (180, 80, 255)),
    FruitType.RARE: FruitData('Rare Spirit Fruit', 3, 20, (255, 210, 60)),
    FruitType.TOXIC: FruitData('Toxic Spirit Fruit', 0, 10, (90, 220, 100)),
}
CONSUMPTION_MESSAGE_SECONDS = 2.5


def choose_fruit_type(rng=None, weights=None):
    """Sample relative weights; inject an RNG or weights for deterministic tests."""
    rng = random if rng is None else rng
    kinds = list(FRUIT_TYPES)
    values = ([FRUIT_TYPES[kind].spawn_weight for kind in kinds] if weights is None
              else [weights[kind] for kind in kinds])
    if any(not math.isfinite(value) or value < 0 for value in values) or sum(values) <= 0:
        raise ValueError('Spawn weights must be finite, nonnegative, and have positive total')
    return rng.choices(kinds, weights=values, k=1)[0]


def create_random_fruit(x, y, rng=None, weights=None):
    return SpiritualFruit(x, y, fruit_type=choose_fruit_type(rng, weights))


class SpiritualFruit:
    def __init__(self, x, y, odor_strength=1.0, capture_radius=CAPTURE_RADIUS,
                 fruit_type=FruitType.COMMON):
        if not math.isfinite(capture_radius) or capture_radius <= 0:
            raise ValueError("capture_radius must be finite and positive")
        self.capture_radius = float(capture_radius)
        self.x = x
        self.y = y
        self.odor_strength = odor_strength
        self.radius = 12
        self.fruit_type = FruitType(fruit_type)
        self.data = FRUIT_TYPES[self.fruit_type]
        self.color = self.data.color

    @property
    def name(self):
        return self.data.name

    @property
    def qi_value(self):
        return self.data.qi_value

    def consumption_message(self):
        reward = f' (+{self.qi_value} Qi)' if self.qi_value else ''
        return f'Consumed {self.name}{reward}'

    def draw(self, screen):
        center = (round(self.x), round(self.y))
        pygame.draw.circle(screen, self.color, center, self.radius)
        if self.fruit_type == FruitType.RARE:
            pygame.draw.circle(screen, (255, 255, 220), center, self.radius - 4, 2)
        elif self.fruit_type == FruitType.TOXIC:
            x, y = center
            pygame.draw.line(screen, (25, 55, 25), (x - 5, y - 5), (x + 5, y + 5), 3)
            pygame.draw.line(screen, (25, 55, 25), (x - 5, y + 5), (x + 5, y - 5), 3)

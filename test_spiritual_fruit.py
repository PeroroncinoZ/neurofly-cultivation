import random
import unittest
from unittest.mock import Mock

from cultivation import Cultivation
from spiritual_fruit import FruitType, SpiritualFruit, create_random_fruit, choose_fruit_type


class FruitTests(unittest.TestCase):
    def test_rewards_and_messages(self):
        qi = 4
        cultivation = Cultivation()
        for kind, reward, message in [
            (FruitType.COMMON, 1, 'Consumed Common Spirit Fruit (+1 Qi)'),
            (FruitType.RARE, 3, 'Consumed Rare Spirit Fruit (+3 Qi)'),
            (FruitType.TOXIC, 0, 'Consumed Toxic Spirit Fruit'),
        ]:
            fruit = SpiritualFruit(10, 20, fruit_type=kind)
            self.assertEqual(fruit.qi_value, reward)
            self.assertEqual(fruit.consumption_message(), message)
            qi += fruit.qi_value
            cultivation.update(qi)
        self.assertEqual(qi, 8)
        self.assertEqual(cultivation.stage, 'Qi Condensation')

    def test_default_weights_are_passed_to_sampler(self):
        rng = Mock()
        rng.choices.return_value = [FruitType.RARE]
        self.assertEqual(choose_fruit_type(rng), FruitType.RARE)
        rng.choices.assert_called_once_with(list(FruitType), weights=[70, 20, 10], k=1)

    def test_weighted_creation_can_select_each_type(self):
        for kind in FruitType:
            weights = {candidate: int(candidate == kind) for candidate in FruitType}
            fruit = create_random_fruit(50, 60, random.Random(42), weights)
            self.assertEqual(fruit.fruit_type, kind)
            self.assertEqual((fruit.x, fruit.y), (50, 60))
            self.assertEqual((fruit.odor_strength, fruit.radius, fruit.capture_radius), (1, 12, 35))

    def test_invalid_weights(self):
        for value in [0, -1, float('nan')]:
            with self.assertRaises(ValueError):
                choose_fruit_type(weights={kind: value for kind in FruitType})

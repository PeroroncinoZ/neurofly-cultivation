import unittest
from cultivation import Cultivation


class CultivationTests(unittest.TestCase):
    def test_just_below_each_threshold(self):
        for qi, stage in [(4, 'Mortal'), (14, 'Qi Condensation'),
                          (34, 'Foundation Establishment')]:
            with self.subTest(qi=qi):
                self.assertEqual(Cultivation().update(qi), stage)

    def test_exact_thresholds(self):
        cultivation = Cultivation()
        for qi, stage in [(5, 'Qi Condensation'), (15, 'Foundation Establishment'),
                          (35, 'Golden Core')]:
            self.assertEqual(cultivation.update(qi), stage)
            self.assertEqual(cultivation.qi, qi)

    def test_multiple_breakthroughs_in_one_update(self):
        cultivation = Cultivation()
        self.assertEqual(cultivation.update(20), 'Foundation Establishment')
        self.assertEqual(cultivation.next_stage_qi, 35)
        self.assertEqual(Cultivation().update(100), 'Golden Core')

    def test_max_stage(self):
        cultivation = Cultivation()
        cultivation.update(35)
        cultivation.update(100)
        self.assertEqual(cultivation.stage, 'Golden Core')
        self.assertIsNone(cultivation.next_stage_qi)
        self.assertEqual(cultivation.display_lines(),
                         ['Cultivation: Golden Core', 'Qi: 100', 'Max stage'])

    def test_progression_never_reverses(self):
        cultivation = Cultivation()
        cultivation.update(15)
        cultivation.update(0)
        self.assertEqual(cultivation.stage, 'Foundation Establishment')
        self.assertEqual(cultivation.qi, 0)

    def test_configurable_thresholds_and_display(self):
        cultivation = Cultivation((0, 2, 4, 8))
        cultivation.update(3)
        self.assertEqual(cultivation.stage, 'Qi Condensation')
        self.assertEqual(cultivation.next_stage_qi, 4)
        self.assertIn('Next stage: 4 total Qi (1 more)', cultivation.display_lines())

    def test_invalid_thresholds(self):
        for thresholds in [(0, 5), (0, 5, 5, 35), (1, 5, 15, 35), (0, -1, 15, 35)]:
            with self.assertRaises(ValueError):
                Cultivation(thresholds)


if __name__ == '__main__':
    unittest.main()

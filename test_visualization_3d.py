"""Synthetic SWC fixtures exercise parsing, not biological morphology."""
import math
from pathlib import Path
import tempfile
import unittest
from brain.visualization_3d import load_skeleton, load_skeletons, project


class VisualizationTests(unittest.TestCase):
    def test_standard_swc_forward_parents_and_coordinates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '123.swc'
            content = '# header\n2 3 405097.16 -20 84.5 0 1\n1 1 1 2 3 4 -1\n'
            path.write_text(content)
            skeleton = load_skeleton(path)
            self.assertEqual(skeleton['nodes'][2], (405097.16, -20, 84.5))
            self.assertEqual(skeleton['edges'], [(2, 1)])
            self.assertEqual(skeleton['metadata'][2]['radius'], 0)
            self.assertEqual(skeleton['skipped_rows'], 0)
            self.assertEqual(path.read_text(), content)

    def test_malformed_rows_are_skipped_and_orphans_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '123.swc'
            path.write_text('1 1 0 0 0 1 -1\ninvalid row\n'
                            '2 3 nan 0 0 1 1\n1 1 0 0 0 1 -1\n'
                            '3 3 1 2 3 1 99\n4 3 3 4 5 0 1\n')
            skeleton = load_skeleton(path)
            self.assertEqual(skeleton['skipped_rows'], 3)
            self.assertEqual(skeleton['invalid_links'], 1)
            self.assertEqual(skeleton['edges'], [(4, 1)])
            self.assertEqual(len(skeleton['nodes']), 3)
            skeletons, errors = load_skeletons(directory, {123: 'loaded', 456: 'missing'})
            self.assertIn(123, skeletons)
            self.assertIn(456, errors)

    def test_empty_file_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / '123.swc').write_text('# no morphology\n')
            _, errors = load_skeletons(directory, {123: 'empty'})
            self.assertIn(123, errors)

    def test_rotation_changes_projection(self):
        self.assertEqual(project((1, 0, 0), 0, 0, 10, (100, 100)), (110, 100))
        self.assertEqual(project((1, 0, 0), math.pi / 2, 0, 10, (100, 100)), (100, 100))

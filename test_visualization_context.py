import tempfile
from pathlib import Path
import unittest
from brain.visualization_context import load_context


class ContextTests(unittest.TestCase):
    def test_missing_has_no_generated_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            mesh, status = load_context(directory)
            self.assertIsNone(mesh)
            self.assertIn('unavailable', status)

    def test_faces_lines_negative_indices_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'brain.obj'
            data = 'v 1 2 3\nv 4 5 6\nv 7 8 9\nf 1/1/1 2/2/1 3/3/1\nl -3 -2\n'
            path.write_text(data)
            mesh, _ = load_context(directory)
            self.assertEqual(mesh['vertices'][0], (1, 2, 3))
            self.assertEqual(len(mesh['edges']), 3)
            self.assertEqual(path.read_text(), data)

    def test_malformed_context_is_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'brain.obj'
            for data in ['v nan 0 0\n', 'v 1 2 3\nl 1 99\n', 'v 1 2 3\nl 0 1\n']:
                path.write_text(data)
                mesh, status = load_context(directory)
                self.assertIsNone(mesh)
                self.assertIn('disabled', status)

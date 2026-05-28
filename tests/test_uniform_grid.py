import unittest

from src.algorithms.uniform_grid import UniformGrid


class TestUniformGrid(unittest.TestCase):
    def test_uniform_grid_creates_with_valid_size(self):
        grid = UniformGrid(width=100, height=80, cell_size=20)

        self.assertEqual(grid.width, 100)
        self.assertEqual(grid.height, 80)
        self.assertEqual(grid.cell_size, 20)
        self.assertEqual(grid.columns, 5)
        self.assertEqual(grid.rows, 4)

    def test_cell_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            UniformGrid(width=100, height=100, cell_size=0)

    def test_width_and_height_must_be_positive(self):
        with self.assertRaises(ValueError):
            UniformGrid(width=0, height=100, cell_size=10)

        with self.assertRaises(ValueError):
            UniformGrid(width=100, height=0, cell_size=10)

    def test_insert_and_query_rect_returns_entity_in_same_cell(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 4, 4, 2, 2)

        self.assertIn(1, grid.query_rect(0, 0, 10, 10))

    def test_query_rect_does_not_return_far_entity(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 80, 80, 4, 4)

        self.assertNotIn(1, grid.query_rect(0, 0, 10, 10))

    def test_object_in_multiple_cells_is_found_from_each_cell(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 8, 8, 8, 8)

        self.assertIn(1, grid.query_rect(0, 0, 2, 2))
        self.assertIn(1, grid.query_rect(15, 0, 2, 2))
        self.assertIn(1, grid.query_rect(0, 15, 2, 2))
        self.assertIn(1, grid.query_rect(15, 15, 2, 2))

    def test_query_rect_returns_set_without_duplicates(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 8, 8, 20, 20)

        self.assertEqual(grid.query_rect(0, 0, 40, 40), {1})

    def test_query_radius_returns_near_entity(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 10, 10, 10, 10)

        self.assertIn(1, grid.query_radius(15, 15, 1))

    def test_query_radius_does_not_return_far_entity(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 80, 80, 10, 10)

        self.assertNotIn(1, grid.query_radius(15, 15, 10))

    def test_clear_removes_cells_and_objects(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 10, 10, 10, 10)

        grid.clear()

        self.assertEqual(grid.objects, {})
        self.assertEqual(grid.query_rect(0, 0, 100, 100), set())

    def test_out_of_bounds_query_does_not_crash(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, 5, 5, 4, 4)

        self.assertIn(1, grid.query_rect(-20, -20, 40, 40))

    def test_partially_out_of_bounds_insert_does_not_crash(self):
        grid = UniformGrid(width=100, height=100, cell_size=10)
        grid.insert(1, -5, -5, 10, 10)

        self.assertIn(1, grid.query_rect(0, 0, 5, 5))


if __name__ == "__main__":
    unittest.main()

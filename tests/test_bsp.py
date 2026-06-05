import unittest

from src.algorithms.bsp import BSPGenerator


class TestBSPGenerator(unittest.TestCase):
    def create_rooms(self, seed=1):
        generator = BSPGenerator(50, 35, seed=seed)
        root = generator.generate_tree()
        generator.create_rooms(root)
        return generator, root, generator.get_rooms(root)

    def rooms_overlap(self, first_room, second_room):
        return (
            first_room.x < second_room.right
            and first_room.right > second_room.x
            and first_room.y < second_room.bottom
            and first_room.bottom > second_room.y
        )

    def test_bsp_generator_creates_root_with_expected_size(self):
        generator = BSPGenerator(50, 35, seed=1)

        root = generator.generate_tree()

        self.assertEqual(root.rect.x, 0)
        self.assertEqual(root.rect.y, 0)
        self.assertEqual(root.rect.width, 50)
        self.assertEqual(root.rect.height, 35)

    def test_bsp_generator_creates_leaf_rooms(self):
        generator, root, rooms = self.create_rooms(seed=1)

        self.assertGreater(len(rooms), 0)
        for leaf in root.leaves():
            self.assertTrue(leaf.is_leaf())
            self.assertIsNotNone(leaf.room)
            self.assertGreaterEqual(leaf.room.width, generator.min_room_size)
            self.assertGreaterEqual(leaf.room.height, generator.min_room_size)

    def test_rooms_are_inside_map_bounds(self):
        _, _, rooms = self.create_rooms(seed=1)

        for room in rooms:
            self.assertGreaterEqual(room.x, 0)
            self.assertGreaterEqual(room.y, 0)
            self.assertLessEqual(room.right, 50)
            self.assertLessEqual(room.bottom, 35)

    def test_rooms_do_not_overlap(self):
        _, _, rooms = self.create_rooms(seed=1)

        for first_index, first_room in enumerate(rooms):
            for second_room in rooms[first_index + 1:]:
                self.assertFalse(self.rooms_overlap(first_room, second_room))

    def test_same_seed_generates_same_rooms(self):
        _, _, first_rooms = self.create_rooms(seed=10)
        _, _, second_rooms = self.create_rooms(seed=10)

        self.assertEqual(first_rooms, second_rooms)

    def test_different_seeds_can_generate_different_rooms(self):
        _, _, first_rooms = self.create_rooms(seed=10)
        _, _, second_rooms = self.create_rooms(seed=11)

        self.assertNotEqual(first_rooms, second_rooms)

    def test_invalid_generator_parameters_raise_value_error(self):
        invalid_parameters = (
            {"width": 19, "height": 15},
            {"width": 20, "height": 14},
            {"width": 20, "height": 15, "min_room_size": 21},
            {
                "width": 20,
                "height": 15,
                "min_leaf_size": 5,
                "min_room_size": 4,
                "room_margin": 1,
            },
            {"width": 20, "height": 15, "max_depth": 0},
        )

        for parameters in invalid_parameters:
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    BSPGenerator(**parameters)


if __name__ == "__main__":
    unittest.main()

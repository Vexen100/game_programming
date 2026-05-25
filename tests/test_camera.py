import unittest

from src.core.camera import Camera


class TestCamera(unittest.TestCase):
    def test_camera_follows_target(self):
        camera = Camera(100, 80)

        camera.follow(200, 160, 400, 300)

        self.assertEqual(camera.x, 150)
        self.assertEqual(camera.y, 120)

    def test_camera_clamps_to_left_and_top_bounds(self):
        camera = Camera(100, 80)

        camera.follow(10, 10, 400, 300)

        self.assertEqual(camera.x, 0)
        self.assertEqual(camera.y, 0)

    def test_camera_clamps_to_right_and_bottom_bounds(self):
        camera = Camera(100, 80)

        camera.follow(390, 290, 400, 300)

        self.assertEqual(camera.x, 300)
        self.assertEqual(camera.y, 220)

    def test_camera_stays_zero_when_map_is_smaller_than_viewport(self):
        camera = Camera(500, 400)

        camera.follow(200, 160, 300, 200)

        self.assertEqual(camera.x, 0)
        self.assertEqual(camera.y, 0)

    def test_camera_apply_offsets_coordinates(self):
        camera = Camera(100, 80)
        camera.x = 20
        camera.y = 10

        self.assertEqual(camera.apply(50, 40), (30, 30))


if __name__ == "__main__":
    unittest.main()

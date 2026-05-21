import unittest

from src.core.scene_manager import SceneManager
from src.scenes.base_scene import BaseScene


class FakeScene(BaseScene):
    pass


class TestSceneManager(unittest.TestCase):
    def test_scene_manager_creates_scene_from_factory(self):
        manager = SceneManager()
        manager.register_scenes({"fake": lambda: FakeScene()})

        manager.request_change("fake")
        manager.process_scene_change()

        self.assertIsInstance(manager.current_scene, FakeScene)
        self.assertIs(manager.current_scene.manager, manager)

    def test_request_change_raises_for_missing_scene(self):
        manager = SceneManager()

        with self.assertRaises(ValueError):
            manager.request_change("missing")

    def test_empty_scene_manager_methods_do_not_crash(self):
        manager = SceneManager()

        manager.handle_events([])
        manager.update(0.1, input_manager=None)
        manager.draw(screen=None)


if __name__ == "__main__":
    unittest.main()

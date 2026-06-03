import unittest

import settings
from src.core.scene_manager import SceneManager
from src.scenes.base_scene import BaseScene


class FakeScene(BaseScene):
    pass


class FakeGameplayScene(BaseScene):
    pass


class FakePauseScene(BaseScene):
    pass


class FakeWorldScene(BaseScene):
    pass


class FakeWorldMapScene(BaseScene):
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

    def test_request_pause_saves_current_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()
        gameplay_scene = manager.current_scene

        manager.request_pause("pause")

        self.assertIs(manager.paused_scene, gameplay_scene)

    def test_request_pause_requests_pause_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()

        manager.request_pause("pause")

        self.assertEqual(manager.next_scene_id, "pause")

    def test_process_scene_change_keeps_paused_scene_for_pause(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()
        gameplay_scene = manager.current_scene

        manager.request_pause("pause")
        manager.process_scene_change()

        self.assertIsInstance(manager.current_scene, FakePauseScene)
        self.assertIs(manager.paused_scene, gameplay_scene)

    def test_resume_scene_restores_gameplay_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()
        gameplay_scene = manager.current_scene
        manager.request_pause("pause")
        manager.process_scene_change()

        manager.resume_scene()

        self.assertIs(manager.current_scene, gameplay_scene)
        self.assertIs(manager.current_scene.manager, manager)
        self.assertIsNone(manager.paused_scene)

    def test_changing_scene_from_pause_clears_paused_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
            "world": lambda: FakeWorldScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()
        manager.request_pause("pause")
        manager.process_scene_change()

        manager.request_change("world")
        manager.process_scene_change()

        self.assertIsInstance(manager.current_scene, FakeWorldScene)
        self.assertIsNone(manager.paused_scene)

    def test_request_pause_does_not_overwrite_existing_paused_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "pause": lambda: FakePauseScene(),
        })
        manager.request_change("gameplay")
        manager.process_scene_change()
        manager.request_pause("pause")
        manager.process_scene_change()
        paused_scene = manager.paused_scene

        manager.request_pause("pause")

        self.assertIs(manager.paused_scene, paused_scene)

    def test_open_world_map_saves_return_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "world_map": lambda: FakeWorldMapScene(),
        })
        gameplay_scene = FakeGameplayScene()

        manager.open_world_map(return_scene=gameplay_scene)

        self.assertIs(manager.world_map_return_scene, gameplay_scene)
        self.assertEqual(manager.next_scene_id, "world_map")

    def test_return_from_world_map_restores_return_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "world_map": lambda: FakeWorldMapScene(),
        })
        gameplay_scene = FakeGameplayScene()
        manager.open_world_map(return_scene=gameplay_scene)
        manager.process_scene_change()

        manager.return_from_world_map()

        self.assertIs(manager.current_scene, gameplay_scene)
        self.assertIs(manager.current_scene.manager, manager)
        self.assertIsNone(manager.world_map_return_scene)

    def test_open_world_map_from_pause_saves_paused_scene_as_return_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            settings.REGION_SCENE: lambda: FakeGameplayScene(),
            settings.PAUSE_SCENE: lambda: FakePauseScene(),
            settings.WORLD_MAP_SCENE: lambda: FakeWorldMapScene(),
        })
        manager.request_change(settings.REGION_SCENE)
        manager.process_scene_change()
        gameplay_scene = manager.current_scene
        manager.request_pause(settings.PAUSE_SCENE)
        manager.process_scene_change()

        manager.open_world_map_from_pause()
        manager.process_scene_change()

        self.assertIsInstance(manager.current_scene, FakeWorldMapScene)
        self.assertIs(manager.world_map_return_scene, gameplay_scene)
        self.assertIsNone(manager.paused_scene)
        self.assertIsNone(manager.pause_scene_id)

    def test_return_from_world_map_after_pause_restores_original_gameplay_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            settings.REGION_SCENE: lambda: FakeGameplayScene(),
            settings.PAUSE_SCENE: lambda: FakePauseScene(),
            settings.WORLD_MAP_SCENE: lambda: FakeWorldMapScene(),
        })
        manager.request_change(settings.REGION_SCENE)
        manager.process_scene_change()
        gameplay_scene = manager.current_scene
        manager.request_pause(settings.PAUSE_SCENE)
        manager.process_scene_change()
        manager.open_world_map_from_pause()
        manager.process_scene_change()

        manager.return_from_world_map()

        self.assertIs(manager.current_scene, gameplay_scene)
        self.assertIs(manager.current_scene.manager, manager)
        self.assertIsNone(manager.world_map_return_scene)

    def test_request_change_clears_world_map_return_scene(self):
        manager = SceneManager()
        manager.register_scenes({
            "gameplay": lambda: FakeGameplayScene(),
            "world_map": lambda: FakeWorldMapScene(),
        })
        manager.world_map_return_scene = FakeGameplayScene()

        manager.request_change("gameplay")

        self.assertIsNone(manager.world_map_return_scene)


if __name__ == "__main__":
    unittest.main()

import unittest

from src.components.components import Animation, AnimationRequest, FacingDirection, Velocity
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.animation_system import AnimationSystem


class TestAnimationSystem(unittest.TestCase):
    """Проверяет runtime idle/walk анимацию сущностей."""

    def create_entity(self, velocity=None, facing=None, animation=None):
        """Создает тестовую сущность с Animation и optional movement data.

        Args:
            velocity: Необязательный компонент скорости.
            facing: Необязательный компонент направления взгляда.
            animation: Необязательный готовый компонент анимации.

        Returns:
            Пара `(ecm, entity_id)`.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, animation or Animation("player"))

        if velocity is not None:
            ecm.add_component(entity, velocity)

        if facing is not None:
            ecm.add_component(entity, facing)

        return ecm, entity

    def test_animation_switches_to_walk_when_velocity_nonzero(self):
        """Проверяет переход в walk при ненулевой скорости.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity(10, 0))

        AnimationSystem().update(ecm, dt=0.01)

        self.assertEqual(ecm.get_component(entity, Animation).state, "walk")

    def test_animation_switches_to_idle_when_velocity_zero(self):
        """Проверяет переход в idle при нулевой скорости.

        Returns:
            None.
        """
        animation = Animation("player", state="walk", frame_index=2, frame_timer=0.1)
        ecm, entity = self.create_entity(velocity=Velocity(), animation=animation)

        AnimationSystem().update(ecm, dt=0.2)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "idle")
        self.assertEqual(animation.frame_index, 0)
        self.assertEqual(animation.frame_timer, 0)

    def test_animation_direction_from_velocity_x(self):
        """Проверяет left/right направление по X-скорости.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity(10, 0))
        system = AnimationSystem()

        system.update(ecm, dt=0.01)
        self.assertEqual(ecm.get_component(entity, Animation).direction, "right")

        ecm.get_component(entity, Velocity).x = -10
        system.update(ecm, dt=0.01)
        self.assertEqual(ecm.get_component(entity, Animation).direction, "left")

    def test_animation_direction_from_velocity_y(self):
        """Проверяет up/down направление по Y-скорости.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity(0, 10))
        system = AnimationSystem()

        system.update(ecm, dt=0.01)
        self.assertEqual(ecm.get_component(entity, Animation).direction, "down")

        ecm.get_component(entity, Velocity).y = -10
        system.update(ecm, dt=0.01)
        self.assertEqual(ecm.get_component(entity, Animation).direction, "up")

    def test_walk_animation_advances_by_delta_time(self):
        """Проверяет смену walk-кадров через deltaTime.

        Returns:
            None.
        """
        animation = Animation("player", state="walk", frame_duration=0.1)
        ecm, entity = self.create_entity(velocity=Velocity(10, 0), animation=animation)

        AnimationSystem().update(ecm, dt=0.25)

        self.assertEqual(ecm.get_component(entity, Animation).frame_index, 2)

    def test_state_or_direction_change_resets_frame_index(self):
        """Проверяет reset кадра при смене направления.

        Returns:
            None.
        """
        animation = Animation(
            "player",
            state="walk",
            direction="right",
            frame_index=2,
            frame_timer=0.05,
        )
        ecm, entity = self.create_entity(velocity=Velocity(0, -10), animation=animation)

        AnimationSystem().update(ecm, dt=0.01)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.direction, "up")
        self.assertEqual(animation.frame_index, 0)

    def test_idle_uses_facing_direction_when_velocity_zero(self):
        """Проверяет idle direction через FacingDirection.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(
            velocity=Velocity(),
            facing=FacingDirection(x=0, y=-1),
        )

        AnimationSystem().update(ecm, dt=0.01)

        self.assertEqual(ecm.get_component(entity, Animation).direction, "up")

    def test_animation_request_switches_to_attack_and_locks(self):
        """Проверяет consume AnimationRequest в attack lock.

        Returns:
            None.
        """
        ecm, entity = self.create_entity()
        ecm.add_component(entity, AnimationRequest("attack", "up", 0.3, 0.075))

        AnimationSystem().update(ecm, dt=0.01)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "attack")
        self.assertEqual(animation.direction, "up")
        self.assertGreater(animation.lock_timer, 0)
        self.assertFalse(ecm.has_component(entity, AnimationRequest))

    def test_locked_attack_animation_not_overridden_by_velocity(self):
        """Проверяет, что velocity не сбивает locked attack.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity(10, 0))
        ecm.add_component(entity, AnimationRequest("attack", "up", 0.3, 0.075))

        AnimationSystem().update(ecm, dt=0.01)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "attack")
        self.assertEqual(animation.direction, "up")

    def test_attack_animation_advances_frames_by_delta_time(self):
        """Проверяет смену кадров attack-анимации через deltaTime.

        Returns:
            None.
        """
        ecm, entity = self.create_entity()
        ecm.add_component(entity, AnimationRequest("attack", "down", 1.0, 0.1))

        AnimationSystem().update(ecm, dt=0.25)

        self.assertEqual(ecm.get_component(entity, Animation).frame_index, 2)

    def test_attack_animation_returns_to_walk_after_lock_expires(self):
        """Проверяет возврат в walk после завершения attack lock.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity(10, 0))
        ecm.add_component(entity, AnimationRequest("attack", "up", 0.05, 0.02))

        AnimationSystem().update(ecm, dt=0.1)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "walk")
        self.assertEqual(animation.direction, "right")

    def test_attack_animation_returns_to_idle_after_lock_expires(self):
        """Проверяет возврат в idle после завершения attack lock.

        Returns:
            None.
        """
        ecm, entity = self.create_entity(velocity=Velocity())
        ecm.add_component(entity, AnimationRequest("attack", "down", 0.05, 0.02))

        AnimationSystem().update(ecm, dt=0.1)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "idle")
        self.assertEqual(animation.frame_index, 0)

    def test_animation_request_restarts_attack_animation(self):
        """Проверяет, что новый request перезапускает attack animation.

        Returns:
            None.
        """
        animation = Animation(
            "player",
            state="attack",
            direction="right",
            frame_index=2,
            frame_timer=0.03,
            lock_timer=0.1,
            lock_duration=0.1,
        )
        ecm, entity = self.create_entity(animation=animation)
        ecm.add_component(entity, AnimationRequest("attack", "left", 0.3, 0.075))

        AnimationSystem().update(ecm, dt=0.01)

        animation = ecm.get_component(entity, Animation)
        self.assertEqual(animation.state, "attack")
        self.assertEqual(animation.direction, "left")
        self.assertEqual(animation.frame_index, 0)
        self.assertGreater(animation.lock_timer, 0.2)

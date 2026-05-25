from src.components.components import FacingDirection, PlayerControlled, Velocity
from src.entities.entities_settings import PlayerSettings


class PlayerInputSystem:
    """Записывает ввод игрока в Velocity"""

    def __init__(self, speed=PlayerSettings.SPEED) -> None:
        self.speed = speed

    def update(self, ecm, input_manager):
        direction = input_manager.get_velocity_direction()

        for entity in ecm.get_entities_with(PlayerControlled, Velocity):
            velocity = ecm.get_component(entity, Velocity)
            velocity.x = direction.x * self.speed
            velocity.y = direction.y * self.speed

            facing_direction = ecm.get_component(entity, FacingDirection)
            if facing_direction is not None and direction.length_squared() > 0:
                if abs(direction.x) >= abs(direction.y):
                    facing_direction.x = 1 if direction.x > 0 else -1
                    facing_direction.y = 0
                else:
                    facing_direction.x = 0
                    facing_direction.y = 1 if direction.y > 0 else -1

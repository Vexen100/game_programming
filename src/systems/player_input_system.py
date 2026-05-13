from src.components.components import PlayerControlled, Velocity
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

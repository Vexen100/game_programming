import pygame

from src.components.components import Position


class DebugOverlay:
    """Рисует отладочную информацию поверх сцены"""

    def __init__(self) -> None:
        self.visible = False
        self.font = pygame.font.Font(None, 22)
        self.color = (255, 255, 0)

    def toggle(self):
        self.visible = not self.visible

    def draw(self, screen, ecm, player_id, tile_map, dt):
        if not self.visible:
            return

        fps = int(1 / dt) if dt > 0 else 0
        position = ecm.get_component(player_id, Position)

        if position is None:
            player_pos_text = "Player pos: -"
            player_tile_text = "Player tile: -"
        else:
            tile_x, tile_y = tile_map.coord_pixels_to_tile(position.x, position.y)
            player_pos_text = f"Player pos: {position.x:.1f}, {position.y:.1f}"
            player_tile_text = f"Player tile: {tile_x}, {tile_y}"

        lines = [
            "DEBUG",
            f"FPS: {fps}",
            f"Entities: {len(ecm.alive_entities)}",
            player_pos_text,
            player_tile_text,
        ]

        for index, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.color)
            screen.blit(text_surface, (10, 60 + index * 18))

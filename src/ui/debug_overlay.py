import pygame

from src.components.components import Position


class DebugOverlay:
    """Рисует отладочные подписи и диагностику сцены.

    """

    def __init__(self) -> None:
        """Инициализирует `DebugOverlay` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.visible = False
        self.font = pygame.font.Font(None, 22)
        self.color = (255, 255, 0)

    def toggle(self):
        """Переключает внутренний флаг или режим.

        Returns:
            None.
        """
        self.visible = not self.visible

    def draw(self, screen, ecm, player_id, tile_map, dt):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            ecm: Менеджер сущностей и компонентов игрового мира.
            player_id: Идентификатор сущности игрока.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
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

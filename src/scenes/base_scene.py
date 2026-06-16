class BaseScene():
    """Описывает игровую сцену: base сцена.

    """
    def __init__(self) -> None:
        """Инициализирует `BaseScene` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        pass

    def handle_events(self, events):
        """Обрабатывает события текущего кадра.

        Args:
            events: Список событий PyGame за текущий кадр.

        Returns:
            None.
        """
        pass

    def update(self, dt, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        pass

    def draw(self, screen):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        pass

class EventBus:
    """Описывает объект проекта: событие bus.

    """

    def __init__(self):
        """Инициализирует `EventBus` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.subscribers = {}

    def subscribe(self, event_type, handler):
        """Подписывает обработчик на события указанного типа.

        Args:
            event_type: Класс события для подписки или отписки.
            handler: Функция-обработчик события.

        Returns:
            None.
        """
        self.subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type, handler):
        """Отписывает обработчик от событий указанного типа.

        Args:
            event_type: Класс события для подписки или отписки.
            handler: Функция-обработчик события.

        Returns:
            None.
        """
        if event_type not in self.subscribers:
            return

        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    def publish(self, event):
        """Публикует событие всем подписчикам его типа.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        event_type = type(event)

        for handler in list(self.subscribers.get(event_type, [])):
            handler(event)

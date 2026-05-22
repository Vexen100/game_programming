class EventBus:
    """Простая шина игровых событий"""

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, handler):
        self.subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type, handler):
        if event_type not in self.subscribers:
            return

        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    def publish(self, event):
        event_type = type(event)

        for handler in list(self.subscribers.get(event_type, [])):
            handler(event)

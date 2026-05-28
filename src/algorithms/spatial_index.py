class SpatialIndex:
    def clear(self):
        raise NotImplementedError

    def insert(self, entity_id, x, y, width=1, height=1):
        raise NotImplementedError

    def query_rect(self, x, y, width, height):
        raise NotImplementedError

    def query_radius(self, x, y, radius):
        raise NotImplementedError

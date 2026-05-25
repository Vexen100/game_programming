class Camera:
    def __init__(self, viewport_width, viewport_height):
        self.x = 0
        self.y = 0
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    def follow(self, target_x, target_y, map_width_pixels, map_height_pixels):
        if map_width_pixels <= self.viewport_width:
            self.x = 0
        else:
            self.x = target_x - self.viewport_width / 2
            self.x = max(0, min(self.x, map_width_pixels - self.viewport_width))

        if map_height_pixels <= self.viewport_height:
            self.y = 0
        else:
            self.y = target_y - self.viewport_height / 2
            self.y = max(0, min(self.y, map_height_pixels - self.viewport_height))

    def apply(self, x, y):
        return x - self.x, y - self.y

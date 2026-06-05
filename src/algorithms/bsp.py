import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RectInt:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def center(self):
        return (
            self.x + self.width // 2,
            self.y + self.height // 2,
        )

    def inset(self, amount):
        return RectInt(
            self.x + amount,
            self.y + amount,
            max(0, self.width - amount * 2),
            max(0, self.height - amount * 2),
        )

    def contains_tile(self, tile):
        tile_x, tile_y = tile
        return (
            self.x <= tile_x < self.right
            and self.y <= tile_y < self.bottom
        )


@dataclass
class BSPNode:
    rect: RectInt
    left: "BSPNode | None" = None
    right: "BSPNode | None" = None
    room: RectInt | None = None

    def is_leaf(self):
        return self.left is None and self.right is None

    def leaves(self):
        if self.is_leaf():
            return [self]

        leaves = []
        if self.left is not None:
            leaves.extend(self.left.leaves())
        if self.right is not None:
            leaves.extend(self.right.leaves())
        return leaves

    def rooms(self):
        rooms = []
        if self.room is not None:
            rooms.append(self.room)

        if self.left is not None:
            rooms.extend(self.left.rooms())
        if self.right is not None:
            rooms.extend(self.right.rooms())

        return rooms


class BSPGenerator:
    def __init__(
        self,
        width,
        height,
        min_leaf_size=8,
        max_depth=4,
        min_room_size=4,
        room_margin=1,
        seed=None,
    ):
        self.width = width
        self.height = height
        self.min_leaf_size = min_leaf_size
        self.max_depth = max_depth
        self.min_room_size = min_room_size
        self.room_margin = room_margin
        self.rng = random.Random(seed)

        self.validate_parameters()

    def validate_parameters(self):
        if self.width < 20:
            raise ValueError("BSP width must be at least 20")
        if self.height < 15:
            raise ValueError("BSP height must be at least 15")
        if self.min_room_size < 1:
            raise ValueError("BSP min_room_size must be at least 1")
        if self.min_room_size > self.width or self.min_room_size > self.height:
            raise ValueError("BSP min_room_size must fit inside the map")
        if self.room_margin < 0:
            raise ValueError("BSP room_margin must not be negative")
        if self.min_leaf_size < self.min_room_size + self.room_margin * 2:
            raise ValueError("BSP min_leaf_size is too small for room settings")
        if self.max_depth < 1:
            raise ValueError("BSP max_depth must be at least 1")

    def generate_tree(self):
        root = BSPNode(RectInt(0, 0, self.width, self.height))
        self.split_node(root, 0)
        return root

    def split_node(self, node, depth):
        if depth >= self.max_depth:
            return

        split_vertical = self.choose_split_direction(node.rect)
        if split_vertical is None:
            return

        rect = node.rect
        if split_vertical:
            split_at = self.rng.randint(
                self.min_leaf_size,
                rect.width - self.min_leaf_size,
            )
            node.left = BSPNode(RectInt(rect.x, rect.y, split_at, rect.height))
            node.right = BSPNode(
                RectInt(
                    rect.x + split_at,
                    rect.y,
                    rect.width - split_at,
                    rect.height,
                )
            )
        else:
            split_at = self.rng.randint(
                self.min_leaf_size,
                rect.height - self.min_leaf_size,
            )
            node.left = BSPNode(RectInt(rect.x, rect.y, rect.width, split_at))
            node.right = BSPNode(
                RectInt(
                    rect.x,
                    rect.y + split_at,
                    rect.width,
                    rect.height - split_at,
                )
            )

        self.split_node(node.left, depth + 1)
        self.split_node(node.right, depth + 1)

    def choose_split_direction(self, rect):
        can_split_vertical = rect.width >= self.min_leaf_size * 2
        can_split_horizontal = rect.height >= self.min_leaf_size * 2

        if not can_split_vertical and not can_split_horizontal:
            return None
        if can_split_vertical and not can_split_horizontal:
            return True
        if can_split_horizontal and not can_split_vertical:
            return False

        if rect.width > rect.height * 1.25:
            return True
        if rect.height > rect.width * 1.25:
            return False

        return self.rng.choice([True, False])

    def create_rooms(self, root):
        for leaf in root.leaves():
            leaf.room = self.create_room_in_leaf(leaf.rect)

    def create_room_in_leaf(self, leaf_rect):
        room_bounds = self.get_room_bounds(leaf_rect)
        room_width = self.rng.randint(self.min_room_size, room_bounds.width)
        room_height = self.rng.randint(self.min_room_size, room_bounds.height)
        room_x = self.rng.randint(room_bounds.x, room_bounds.right - room_width)
        room_y = self.rng.randint(room_bounds.y, room_bounds.bottom - room_height)
        return RectInt(room_x, room_y, room_width, room_height)

    def get_room_bounds(self, leaf_rect):
        room_bounds = leaf_rect.inset(self.room_margin)

        if (
            room_bounds.width >= self.min_room_size
            and room_bounds.height >= self.min_room_size
        ):
            return room_bounds

        return leaf_rect

    def get_rooms(self, root):
        return root.rooms()

# Настройки окна
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "Crown Reclaim"
FPS = 60

# Цвета (RGB кортежи для оптимизации без строк)
BG_COLOR = (255, 0, 0)       # red
WALL_COLOR = (128, 128, 128)  # gray
FLOOR_COLOR = (0, 128, 0)    # green
GRASS_COLOR = (60, 145, 70)
DIRT_COLOR = (125, 92, 55)
ROAD_COLOR = (150, 130, 85)
RUINS_FLOOR_COLOR = (112, 112, 105)
WATER_COLOR = (40, 90, 150)
FOREST_COLOR = (35, 95, 55)
BRIDGE_COLOR = (135, 105, 65)
UNKNOWN_TILE_COLOR = (255, 0, 255)


# Константы для actions (для InputManager)
MOVE_UP = "up"
MOVE_LEFT = "left"
MOVE_DOWN = "down"
MOVE_RIGHT = "right"
PAUSE = "pause"
DEBUG = "debug"
ATTACK = "attack"
INTERACT = "interact"
RESTART = "restart"
SELECT = "select"
START_ASSAULT = "start_assault"
OPEN_WORLD_MAP = "open_world_map"
TOGGLE_FULLSCREEN = "toggle_fullscreen"

# Размер тайлов для карты
TILE_SIZE = 32

# Константы для сцен (названия сцен)
MAIN_MENU_SCENE = "main_menu"
WORLD_MAP_SCENE = "world_map"
REGION_SCENE = "region"
CASTLE_ASSAULT_SCENE = "castle_assault"
PAUSE_SCENE = "pause"

# Пути к данным
REGIONS_DATA_PATH = "data/regions/regions.json"
SAVE_FILE_PATH = "data/saves/save_1.json"

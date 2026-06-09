from dataclasses import dataclass


@dataclass
class Position:
    """Хранит данные ECS-компонента: position.

    Attributes:
        x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
        y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
    """
    x: float
    y: float


@dataclass
class Velocity:
    """Хранит данные ECS-компонента: скорость.

    Attributes:
        x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
        y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
    """
    x: float = 0
    y: float = 0


@dataclass
class Collider:
    """Хранит данные ECS-компонента: collider.

    Attributes:
        width: Ширина области, карты или изображения.
        height: Высота области, карты или изображения.
        solid: Флаг, показывающий, участвует ли коллайдер в столкновениях.
    """
    width: int
    height: int
    solid: bool = True


@dataclass
class Renderable:
    """Описывает объект проекта: renderable.

    Attributes:
        width: Ширина области, карты или изображения.
        height: Высота области, карты или изображения.
        color: Цвет `цвет` в формате PyGame.
    """
    width: int
    height: int
    color: tuple[int, int, int]


@dataclass
class Sprite:
    """Описывает объект проекта: sprite.

    Attributes:
        asset_key: Ключ графического ассета сущности.
    """
    asset_key: str


@dataclass
class Health:
    """Хранит данные ECS-компонента: health.

    Attributes:
        current: Значение `текущий`, используемое в логике метода.
        maximum: Максимально допустимое значение.
    """
    current: int
    maximum: int


@dataclass
class PlayerControlled:
    """Описывает объект проекта: игрок controlled.

    """
    pass


@dataclass
class PlayerDefeated:
    """Описывает объект проекта: игрок defeated.

    """
    pass


@dataclass
class Enemy:
    """Описывает объект проекта: враг.

    """
    pass


@dataclass
class EnemyAttackState:
    """Хранит состояние: враг атака состояние.

    Attributes:
        windup_duration: Длительность подготовки атаки.
        windup_timer: Таймер подготовки атаки.
        recovery_timer: Таймер восстановления после атаки.
        pending: Флаг отложенного действия.
    """
    windup_duration: float = 0.35
    windup_timer: float = 0
    recovery_timer: float = 0
    pending: bool = False


@dataclass
class Outpost:
    """Описывает объект проекта: аванпост.

    Attributes:
        radius: Радиус области действия или отрисовки.
        cleared: Флаг, показывающий, зачищен ли аванпост.
        clear_duration: Время, необходимое для зачистки объекта.
        clear_progress: Текущий прогресс зачистки объекта.
    """
    radius: float
    cleared: bool = False
    clear_duration: float = 1.2
    clear_progress: float = 0


@dataclass
class NPC:
    """Описывает объект проекта: NPC.

    Attributes:
        interaction_radius: Радиус, в котором игрок может взаимодействовать с объектом.
        quest_id: Идентификатор задания NPC.
        required_outpost_id: Идентификатор аванпоста, необходимого для задания NPC.
        quest_completed: Флаг, показывающий, выполнено ли задание NPC.
        report_duration: Время, необходимое для сдачи задания NPC.
        report_progress: Текущий прогресс сдачи задания NPC.
    """
    interaction_radius: float
    quest_id: str
    required_outpost_id: int | None = None
    quest_completed: bool = False
    report_duration: float = 0.8
    report_progress: float = 0


@dataclass
class CapturePoint:
    """Описывает объект проекта: точка захвата точка.

    Attributes:
        radius: Радиус области действия или отрисовки.
        progress: Текущий накопленный прогресс действия.
        owner: Текущий владелец точки захвата.
        captured: Флаг, показывающий, захвачена ли точка игроком.
    """
    radius: float
    progress: float = 0
    owner: str = "enemy"
    captured: bool = False


@dataclass
class Dead:
    """Описывает объект проекта: dead.

    """
    pass


@dataclass
class ChaseBehavior:
    """Описывает объект проекта: chase behavior.

    Attributes:
        speed: Скорость движения сущности.
        detection_radius: Радиус обнаружения игрока врагом.
    """
    speed: float
    detection_radius: float


@dataclass
class PatrolRoute:
    """Описывает объект проекта: патруль route.

    Attributes:
        patrol_tiles: Маршрут патруля как список тайлов.
        current_index: Текущий индекс в списке или маршруте.
        wait_duration: Значение `wait duration`, используемое в логике метода.
        wait_timer: Значение `wait таймер`, используемое в логике метода.
    """
    patrol_tiles: list[tuple[int, int]]
    current_index: int = 0
    wait_duration: float = 0
    wait_timer: float = 0


@dataclass
class AttackIntent:
    """Описывает объект проекта: атака intent.

    Attributes:
        requested: Флаг, показывающий, что действие было запрошено.
    """
    requested: bool = False


@dataclass
class FacingDirection:
    """Описывает объект проекта: facing direction.

    Attributes:
        x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
        y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
    """
    x: int = 1
    y: int = 0


@dataclass
class AttackHitbox:
    """Описывает объект проекта: атака hitbox.

    Attributes:
        active: Флаг активности состояния или hitbox.
        x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
        y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
        width: Ширина области, карты или изображения.
        height: Высота области, карты или изображения.
        timer: Текущее значение таймера в секундах.
        duration: Длительность действия или таймера в секундах.
        hit_landed: Флаг, показывающий, было ли уже засчитано попадание.
    """
    active: bool = False
    x: float = 0
    y: float = 0
    width: int = 0
    height: int = 0
    timer: float = 0
    duration: float = 0.12
    hit_landed: bool = False


@dataclass
class MeleeAttack:
    """Описывает объект проекта: melee атака.

    Attributes:
        damage: Количество урона, наносимое атакой.
        attack_range: Дальность атаки.
        cooldown: Время перезарядки действия в секундах.
        cooldown_timer: Оставшееся время перезарядки.
        knockback_distance: Дистанция отталкивания цели после попадания.
    """
    damage: int
    attack_range: float
    cooldown: float
    cooldown_timer: float = 0
    knockback_distance: float = 0

from dataclasses import dataclass, field


PLAYER_CONTROL = "player"
ENEMY_CONTROL = "enemy"
LOCKED_CONTROL = "locked"


@dataclass
class RegionState:
    """Хранит прогресс отдельного региона на глобальной карте.

    Attributes:
        id: Идентификатор объекта `id`.
        name: Значение `name`, используемое в логике метода.
        unlocked: Флаг, показывающий, открыт ли регион.
        control_state: Текущее состояние контроля региона.
        player_influence: Текущее влияние игрока в регионе.
        enemy_influence: Текущее влияние врага в регионе.
        assault_unlocked: Флаг доступности штурма замка в регионе.
        liberated: Флаг, показывающий, освобожден ли регион.
        unlocks_on_liberation: Список регионов, открываемых после освобождения.
    """
    id: str
    name: str
    unlocked: bool
    control_state: str
    player_influence: int
    enemy_influence: int
    assault_unlocked: bool
    liberated: bool
    unlocks_on_liberation: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        """Создает объект из словаря сериализованных данных.

        Args:
            data: Словарь или структура данных из JSON или другого источника.

        Returns:
            Восстановленный объект нужного типа.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            unlocked=data["unlocked"],
            control_state=data["control_state"],
            player_influence=data["player_influence"],
            enemy_influence=data["enemy_influence"],
            assault_unlocked=data["assault_unlocked"],
            liberated=data["liberated"],
            unlocks_on_liberation=data.get("unlocks_on_liberation", []),
        )

    def to_dict(self):
        """Преобразует объект в словарь для сериализации.

        Returns:
            Словарь с сериализованным состоянием объекта.
        """
        return {
            "id": self.id,
            "name": self.name,
            "unlocked": self.unlocked,
            "control_state": self.control_state,
            "player_influence": self.player_influence,
            "enemy_influence": self.enemy_influence,
            "assault_unlocked": self.assault_unlocked,
            "liberated": self.liberated,
            "unlocks_on_liberation": list(self.unlocks_on_liberation),
        }

from dataclasses import dataclass, field


PLAYER_CONTROL = "player"
ENEMY_CONTROL = "enemy"
LOCKED_CONTROL = "locked"


@dataclass
class RegionState:
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

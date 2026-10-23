from dataclasses import dataclass


@dataclass
class Player:
    name: str
    id: int | None = None

    @property
    def has_id(self) -> bool:
        return self.id is not None


@dataclass
class Game:
    name: str
    is_collective: bool
    id: int | None = None

    @property
    def has_id(self) -> bool:
        return self.id is not None


@dataclass
class Match:
    players_id: list[int]
    players_score: list[int | None]
    game_id: int
    collective_score: int | None = None
    id: int | None = None
    opponent_match_id: int | None = None

    @property
    def has_id(self) -> bool:
        return self.id is not None

import logging

from .models import Game, Match, Player
from .postgre import PostgreHandler
from .redis import RedisHandler

logger = logging.getLogger(__name__)


class StorageHandler:
    def __init__(self, config: dict) -> None:
        self.redis = RedisHandler(config["REDIS_URL"])
        self.postgre = PostgreHandler(
            config["POSTGRE_URL"],
            config["POSTGRE_USER"],
            config["POSTGRE_PASSWORD"],
        )

    def add_match(
        self,
        game: Game,
        players: list[Player],
        players_score: list[int] | None = None,
        collective_score: int | None = None,
        opponent_match_id: int | None = None,
    ) -> bool:
        if not game.has_id or not all(p.has_id for p in players):
            raise ValueError("missing id")
        if game.is_collective:
            if collective_score is None:
                raise ValueError("A collective score is required")
            match_players_score = [None] * len(players)
        elif collective_score is not None:
            raise ValueError("Individual matches cannot have a collective score")
        elif players_score is None or len(players) != len(players_score):
            raise ValueError("players and scores must have the same length")
        else:
            match_players_score = players_score
        match = Match(
            game_id=game.id,
            players_id=[p.id for p in players],
            players_score=match_players_score,
            collective_score=collective_score,
        )
        success, match = self.postgre.add_match(match, opponent_match_id)
        if success:
            logging.info(f"Match {match.id} added to PostgreSQL database.")
            self.redis.add_match(game, match)
        return success

    def add_game(self, name: str, is_collective: bool) -> bool:
        if name.isspace() or name == "":
            raise ValueError
        return self.postgre.add_game(Game(name=name, is_collective=is_collective))

    def add_player(self, name: str) -> bool:
        if name.isspace() or name == "":
            raise ValueError
        return self.postgre.add_player(Player(name=name))

    def get_player_by_name(self, name: str) -> Player | None:
        return self.postgre.get_player_by_name(name)

    def get_game_by_name(self, name: str) -> Game | None:
        return self.postgre.get_game_by_name(name)

    def get_last_matchs(self, game: Game | None = None) -> list[Match]:
        if game is not None and not game.has_id:
            raise ValueError
        result = self.redis.get_last_matchs(game)
        return self._get_matches_in_id_order(result)

    def _get_matches_in_id_order(self, match_ids: list[int]) -> list[Match]:
        matches = self.postgre.get_matches_by_ids(match_ids)
        matches_by_id = {match.id: match for match in matches}
        return [
            matches_by_id[match_id]
            for match_id in match_ids
            if match_id in matches_by_id
        ]

    def get_players_by_ids(self, player_ids: list[int]) -> list[Player | None]:
        players = self.postgre.get_players_by_ids(player_ids)
        players_by_id = {player.id: player for player in players}
        return [players_by_id.get(player_id) for player_id in player_ids]

    def get_match_by_id(self, match_id: int) -> Match | None:
        return self.postgre.get_match_by_id(match_id)

    def get_game_by_id(self, game_id: int) -> Game | None:
        return self.postgre.get_game_by_id(game_id)

    def get_player_by_id(self, player_id: int) -> Player | None:
        return self.postgre.get_player_by_id(player_id)

    def list_players(self) -> list[Player]:
        return self.postgre.list_players()

    def list_games(self) -> list[Game]:
        return self.postgre.list_games()

    def list_matches(self) -> list[Match]:
        return self.postgre.list_matches()

    def get_matches_by_player(self, player: Player) -> list[Match]:
        return self.postgre.get_matches_by_player(player)

    def get_play_number(self, game: Game) -> int:
        if not game.has_id:
            raise ValueError
        return self.redis.get_number_of_matches(game)

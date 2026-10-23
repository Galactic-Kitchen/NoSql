from redis import Redis

from .models import Game, Match


class RedisHandler:
    GLOBAL_LAST_MATCHES = "global_matches"

    def __init__(self, url: str) -> None:
        self.conn = Redis(host=url, decode_responses=True)
        self.conn.set_response_callback("GET", int)
        self.conn.set_response_callback(
            "LRANGE",
            lambda response: [int(match_id) for match_id in response],
        )

    def _format_game_key(self, key: int) -> str:
        return f"g_{key}"

    def _format_match_key(self, key: int) -> str:
        return f"m_{key}"

    def get_number_of_matches(self, game: Game) -> int:
        return self.conn.get(self._format_game_key(game.id)) or 0

    def add_match(self, game: Game, match: Match) -> None:
        gkey = self._format_game_key(game.id)
        mkey = self._format_match_key(game.id)

        self.conn.incr(gkey, 1)
        self.conn.lpush(mkey, match.id)
        self.conn.lpush(self.GLOBAL_LAST_MATCHES, match.id)

    def get_last_matchs(
        self,
        game: Game | None = None,
        quantity: int = 10,
    ) -> list[int]:
        if game is None:
            key = self.GLOBAL_LAST_MATCHES
        else:
            key = self._format_match_key(game.id)
        return self.conn.lrange(key, 0, quantity - 1)

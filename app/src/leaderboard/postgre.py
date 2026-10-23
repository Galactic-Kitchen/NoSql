import logging

from psycopg import Connection, Error, connect

from .models import Game, Match, Player

logger = logging.getLogger(__name__)


class PostgreHandler:
    """Main class for handling postgresql operations

    Takes dataclasses into inputs, discarding relatives id in favor of postgresql handling them
    It isn't designed to suppot real use cases for things like upgrade or authentification.
    """

    DBNAME = "leaderboard"

    def __init__(self, url: str, user: str, password: str) -> None:
        self.conn: Connection = connect(
            host=url,
            user=user,
            password=password,
            dbname=self.DBNAME,
            connect_timeout=10,
            autocommit=True,
        )

    def list_players(self) -> list[Player]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM players ORDER BY id")
            return [Player(id=row[0], name=row[1]) for row in cur.fetchall()]

    def list_games(self) -> list[Game]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, is_collective FROM games ORDER BY id")
            return [
                Game(id=row[0], name=row[1], is_collective=row[2])
                for row in cur.fetchall()
            ]

    def list_matches(self) -> list[Match]:
        query = "SELECT m.id, m.game_id, ARRAY_AGG(mp.player_id ORDER BY mp.player_id), ARRAY_AGG(mp.player_score ORDER BY mp.player_id), m.opponent_match_id, m.collective_score FROM matches AS m INNER JOIN match_players AS mp ON mp.match_id = m.id GROUP BY m.id ORDER BY m.id"

        with self.conn.cursor() as cur:
            cur.execute(query)
            return [
                Match(
                    id=row[0],
                    game_id=row[1],
                    players_id=row[2],
                    players_score=row[3],
                    opponent_match_id=row[4],
                    collective_score=row[5],
                )
                for row in cur.fetchall()
            ]

    def get_matches_by_player(self, player: Player) -> list[Match]:
        if not player.has_id:
            raise ValueError("Player must have an id")

        query = """
            SELECT m.id, m.game_id,
                   ARRAY_AGG(mp.player_id ORDER BY mp.player_id),
                   ARRAY_AGG(mp.player_score ORDER BY mp.player_id),
                   m.opponent_match_id,
                   m.collective_score
            FROM matches AS m
            INNER JOIN match_players AS mp ON mp.match_id = m.id
            WHERE EXISTS (
                SELECT 1
                FROM match_players AS player_match
                WHERE player_match.match_id = m.id
                  AND player_match.player_id = %s
            )
            GROUP BY m.id
            ORDER BY m.id DESC
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (player.id,))
            return [
                Match(
                    id=row[0],
                    game_id=row[1],
                    players_id=row[2],
                    players_score=row[3],
                    opponent_match_id=row[4],
                    collective_score=row[5],
                )
                for row in cur.fetchall()
            ]

    def get_player_by_name(self, name: str) -> Player | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM players WHERE name = %s", (name,))
            row = cur.fetchone()
        return Player(id=row[0], name=row[1]) if row is not None else None

    def get_game_by_name(self, name: str) -> Game | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, is_collective FROM games WHERE name = %s",
                (name,),
            )
            row = cur.fetchone()
        return Game(id=row[0], name=row[1], is_collective=row[2]) if row else None

    def get_match_by_id(self, match_id: int) -> Match | None:
        query = "SELECT m.id, m.game_id, ARRAY_AGG(mp.player_id ORDER BY mp.player_id), ARRAY_AGG(mp.player_score ORDER BY mp.player_id), m.opponent_match_id, m.collective_score FROM matches AS m INNER JOIN match_players AS mp ON mp.match_id = m.id WHERE m.id = %s GROUP BY m.id"
        with self.conn.cursor() as cur:
            cur.execute(query, (match_id,))
            row = cur.fetchone()
        return (
            Match(
                id=row[0],
                game_id=row[1],
                players_id=row[2],
                players_score=row[3],
                opponent_match_id=row[4],
                collective_score=row[5],
            )
            if row is not None
            else None
        )

    def get_matches_by_ids(self, match_ids: list[int]) -> list[Match]:
        if not match_ids:
            return []

        query = "SELECT m.id, m.game_id, ARRAY_AGG(mp.player_id ORDER BY mp.player_id), ARRAY_AGG(mp.player_score ORDER BY mp.player_id), m.opponent_match_id, m.collective_score FROM matches AS m INNER JOIN match_players AS mp ON mp.match_id = m.id WHERE m.id = ANY(%s) GROUP BY m.id"
        with self.conn.cursor() as cur:
            cur.execute(query, (match_ids,))
            return [
                Match(
                    id=row[0],
                    game_id=row[1],
                    players_id=row[2],
                    players_score=row[3],
                    opponent_match_id=row[4],
                    collective_score=row[5],
                )
                for row in cur.fetchall()
            ]

    def get_game_by_id(self, game_id: int) -> Game | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, is_collective FROM games WHERE id = %s",
                (game_id,),
            )
            row = cur.fetchone()
        return Game(id=row[0], name=row[1], is_collective=row[2]) if row else None

    def get_player_by_id(self, player_id: int) -> Player | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM players WHERE id = %s", (player_id,))
            row = cur.fetchone()
        return Player(id=row[0], name=row[1]) if row else None

    def get_players_by_ids(self, player_ids: list[int]) -> list[Player]:
        if not player_ids:
            return []

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM players WHERE id = ANY(%s)",
                (player_ids,),
            )
            return [Player(id=row[0], name=row[1]) for row in cur.fetchall()]

    def add_game(self, game: Game) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO games (name, is_collective) VALUES (%s, %s)",
                    (game.name, game.is_collective),
                )
            return True
        except Error:
            logger.exception("Could not add game to PostgreSQL.")
            return False

    def add_player(self, player: Player) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (name) VALUES (%s)",
                    (player.name,),
                )
            return True
        except Error:
            logger.exception("Could not add player to PostgreSQL.")
            return False

    def add_match(
        self,
        match: Match,
        opponent_match_id: int | None = None,
    ) -> tuple[bool, Match | None]:
        try:
            with self.conn.transaction(), self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO matches (game_id, opponent_match_id, collective_score) VALUES (%s, %s, %s) RETURNING id",
                    (match.game_id, opponent_match_id, match.collective_score),
                )
                match_id = cur.fetchone()[0]

                cur.executemany(
                    "INSERT INTO match_players (match_id, player_id, player_score) VALUES (%s, %s, %s)",
                    [
                        (match_id, pid, score)
                        for pid, score in zip(
                            match.players_id,
                            match.players_score,
                            strict=True,
                        )
                    ],
                )
                if opponent_match_id is not None:
                    cur.execute(
                        "UPDATE matches SET opponent_match_id = %s WHERE id = %s",
                        (match_id, opponent_match_id),
                    )

            return True, Match(
                players_id=match.players_id,
                players_score=match.players_score,
                game_id=match.game_id,
                id=match_id,
                opponent_match_id=opponent_match_id,
                collective_score=match.collective_score,
            )
        except Error:
            logger.exception("Could not add match to PostgreSQL.")
            return False, None

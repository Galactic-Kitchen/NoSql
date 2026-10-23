from dataclasses import dataclass

from .models import Game
from .storage import StorageHandler


@dataclass(frozen=True)
class MatchSubmission:
    game_id: int
    players_id: list[int]
    players_score_raw: list[str]
    collective_score_raw: str | None
    opponent_match_id: int | None


def _parse_scores(
    is_collective: bool,
    player_count: int,
    players_score_raw: list[str],
    collective_score_raw: str | None,
) -> tuple[list[int] | None, int | None]:
    if is_collective:
        if not collective_score_raw:
            raise ValueError("Provide the total team score.")
        try:
            return None, int(collective_score_raw)
        except ValueError as error:
            raise ValueError("Scores must be integers.") from error
    if not players_score_raw:
        raise ValueError("Provide a score for each player.")
    try:
        players_score = [int(score) for score in players_score_raw]
    except ValueError as error:
        raise ValueError("Scores must be integers.") from error
    if len(players_score) != player_count:
        raise ValueError("Provide exactly one score for each player.")
    return players_score, None


def record_match(
    store: StorageHandler,
    submission: MatchSubmission,
) -> Game:
    game = store.get_game_by_id(submission.game_id)
    if not game:
        raise ValueError("The selected game no longer exists.")
    if submission.opponent_match_id is not None:
        opponent_match = store.get_match_by_id(submission.opponent_match_id)
        if not opponent_match or opponent_match.game_id != game.id:
            raise ValueError("Choose an opponent match from the selected game.")

    players_score, collective_score = _parse_scores(
        is_collective=game.is_collective,
        player_count=len(submission.players_id),
        players_score_raw=submission.players_score_raw,
        collective_score_raw=submission.collective_score_raw,
    )

    players = [
        store.get_player_by_id(player_id) for player_id in submission.players_id
    ]
    if any(player is None for player in players):
        raise ValueError("One or more selected players no longer exist.")
    resolved_players = [player for player in players if player is not None]
    if not store.add_match(
        game,
        resolved_players,
        players_score,
        collective_score,
        submission.opponent_match_id,
    ):
        raise ValueError("Could not save the match.")
    return game

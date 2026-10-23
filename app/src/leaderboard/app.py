import logging
from datetime import datetime
from secrets import token_urlsafe

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from .services import MatchSubmission, record_match
from .storage import StorageHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("leaderboard").setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_prefixed_env()
if not app.config.get("SECRET_KEY"):
    app.config["SECRET_KEY"] = token_urlsafe(32)
CSRFProtect(app)
store: StorageHandler = StorageHandler(app.config)


@app.context_processor
def inject_current_year() -> dict:
    return {"current_year": datetime.now().astimezone().year}


def form_error(message: str):
    flash(message, "error")
    return redirect(url_for("adder_dispatcher"), code=303)


@app.route("/", methods=["GET"])
def index():
    last_matches = store.get_last_matchs()
    return render_template("index.html", last_matches=last_matches)


@app.route("/info", methods=["GET"])
def info():
    return render_template("info.html")


@app.route("/player", methods=["POST"])
def new_player():
    name = request.form.get("name")
    if not name:
        return form_error("Enter a player name.")
    try:
        success = store.add_player(name)
        if success:
            flash("Player added successfully.", "success")
            return redirect(url_for("index"), code=303)
        return form_error("Could not add the player. The name may already exist.")
    except ValueError:
        return form_error("Enter a valid player name.")


def parse_match_ids() -> tuple[int, list[int], int | None]:
    game_id_raw = request.form.get("game_id")
    players_id_raw = request.form.getlist("players_id")
    opponent_match_id_raw = request.form.get("opponent_match_id")
    if not game_id_raw or not players_id_raw:
        raise ValueError("Select a game and at least one player.")
    try:
        return (
            int(game_id_raw),
            [int(player_id) for player_id in players_id_raw],
            int(opponent_match_id_raw) if opponent_match_id_raw else None,
        )
    except ValueError as error:
        raise ValueError("Match and player IDs must be integers.") from error


@app.route("/game", methods=["POST"])
def new_game():
    name = request.form.get("name")
    is_collective = request.form.get("is_collective")
    if not name:
        return form_error("Enter a game name.")
    if isinstance(is_collective, str):
        if is_collective.lower() not in {"true", "false"}:
            return form_error("Choose a valid game type.")
        is_collective = is_collective.lower() == "true"
    try:
        success = store.add_game(name, is_collective)
        if success:
            flash("Game added successfully.", "success")
            return redirect(url_for("list_games"), code=303)
        return form_error("Could not add the game. The name may already exist.")
    except ValueError:
        return form_error("Enter valid game details.")


@app.route("/match", methods=["POST"])
def new_match():
    try:
        game_id, players_id, opponent_match_id = parse_match_ids()
        game = record_match(
            store,
            MatchSubmission(
                game_id=game_id,
                players_id=players_id,
                players_score_raw=request.form.getlist("players_score"),
                collective_score_raw=request.form.get("collective_score"),
                opponent_match_id=opponent_match_id,
            ),
        )
    except ValueError as error:
        return form_error(str(error))
    flash("Match recorded successfully.", "success")
    return redirect(url_for("get_game", game_id=game.id), code=303)


@app.route("/match/<int:match_id>", methods=["GET"])
def get_match(match_id: int):
    match = store.get_match_by_id(match_id)
    if not match:
        return {"error": "Match not found"}, 404
    game = store.get_game_by_id(match.game_id)
    players = store.get_players_by_ids(match.players_id)
    opponent = (
        store.get_match_by_id(match.opponent_match_id)
        if match.opponent_match_id is not None
        else None
    )
    return render_template(
        "match.html",
        match=match,
        game=game,
        players=players,
        opponent=opponent,
    )


@app.route("/game/<int:game_id>", methods=["GET"])
def get_game(game_id: int):
    game = store.get_game_by_id(game_id)
    last_matches = store.get_last_matchs(game=game)
    if not game:
        return {"error": "Game not found"}, 404
    return render_template("game.html", game=game, last_matches=last_matches)


@app.route("/player/<int:player_id>", methods=["GET"])
def get_player(player_id: int):
    player = store.get_player_by_id(player_id)
    if not player:
        return {"error": "Player not found"}, 404
    matches = store.get_matches_by_player(player)
    games_by_id = {game.id: game for game in store.list_games()}
    return render_template(
        "player.html",
        player=player,
        matches=matches,
        games_by_id=games_by_id,
    )


@app.route("/players", methods=["GET"])
def list_players():
    players = store.list_players()
    return render_template("players.html", players=players)


@app.route("/games", methods=["GET"])
def list_games():
    games = store.list_games()
    return render_template("games.html", games=games)


@app.route("/new", methods=["GET"])
def adder_dispatcher():
    return render_template(
        "new.html",
        games=store.list_games(),
        players=store.list_players(),
        matches=store.list_matches(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

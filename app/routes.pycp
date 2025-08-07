
import os
from flask import Blueprint, render_template, jsonify, request
import chess.pgn
import threading
import queue
import time
from stockfish import Stockfish

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file if present

GAMES_DIR = os.getenv("GAMES_DIR", "/root/chess-api/games")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")

main = Blueprint("main", __name__)

# Stockfish instance using the python-stockfish package (recommended)
stockfish = Stockfish(path=STOCKFISH_PATH, depth=15)

def safe_join(base, *paths):
    # Prevent path traversal
    final_path = os.path.abspath(os.path.join(base, *paths))
    if not final_path.startswith(os.path.abspath(base)):
        raise ValueError("Unsafe path detected")
    return final_path

@main.route("/")
def index():
    players = {}
    for player in os.listdir(GAMES_DIR):
        player_path = os.path.join(GAMES_DIR, player)
        if not os.path.isdir(player_path):
            continue
        players[player] = {}
        for date in os.listdir(player_path):
            date_path = os.path.join(player_path, date)
            if not os.path.isdir(date_path):
                continue
            players[player][date] = [
                f for f in os.listdir(date_path) if f.endswith(".pgn")
            ]
    return render_template("index.html", players=players)

@main.route("/viewer")
def viewer():
    player = request.args.get("player")
    date = request.args.get("date")
    file = request.args.get("file")
    if not player or not date or not file:
        return "Missing parameters", 400
    return render_template("viewer.html", player=player, date=date, filename=file)

@main.route("/load_game", methods=["POST"])
def load_game():
    data = request.get_json()
    player = data.get("player")
    date = data.get("date")
    filename = data.get("filename")
    if not player or not date or not filename:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        game_path = safe_join(GAMES_DIR, player, date, filename)
    except ValueError:
        return jsonify({"error": "Invalid file path"}), 400

    if not os.path.exists(game_path):
        return jsonify({"error": "Game not found"}), 404

    with open(game_path, "r") as f:
        game = chess.pgn.read_game(f)

    moves = []
    board = game.board()
    for move in game.mainline_moves():
        san = board.san(move)
        board.push(move)
        moves.append({
            "move": san,
            "fen": board.fen()
        })
    return jsonify(moves)

@main.route("/analyze_fen", methods=["POST"])
def analyze_fen_route():
    data = request.get_json()
    fen = data.get("fen")
    if not fen:
        return jsonify({"error": "Missing FEN"}), 400

    try:
        stockfish.set_fen_position(fen)
        info = stockfish.get_evaluation()
        best_move = stockfish.get_best_move()
        return jsonify({
            "score": info.get("value"),
            "type": info.get("type"),
            "best_move": best_move
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import os
from flask import Blueprint, render_template, jsonify, request
import chess.pgn
import subprocess
import threading
import queue
import time
from stockfish import Stockfish

GAMES_DIR = "/root/chess-api/games"
STOCKFISH_PATH = "/usr/games/stockfish"  # path to your stockfish binary

main = Blueprint("main", __name__)

# Globals for stockfish process management
stockfish_process = None
output_queue = queue.Queue()
listener_thread = None
stockfish = Stockfish(path=STOCKFISH_PATH, depth=15)

def start_stockfish():
    global stockfish_process, listener_thread, output_queue
    if stockfish_process:
        return  # already started

    stockfish_process = subprocess.Popen(
        [STOCKFISH_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
    )

    def listen():
        while True:
            line = stockfish_process.stdout.readline()
            if line:
                output_queue.put(line.strip())
            else:
                break

    listener_thread = threading.Thread(target=listen, daemon=True)
    listener_thread.start()

    # Initialize UCI
    send_command("uci")
    wait_for("uciok")
    send_command("isready")
    wait_for("readyok")

def stop_stockfish():
    global stockfish_process
    if stockfish_process:
        send_command("quit")
        stockfish_process.terminate()
        stockfish_process.wait()
        stockfish_process = None

def send_command(command):
    global stockfish_process
    if stockfish_process and stockfish_process.stdin:
        stockfish_process.stdin.write(command + "\n")
        stockfish_process.stdin.flush()

def wait_for(text, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        try:
            line = output_queue.get(timeout=timeout)
            if text in line:
                return line
        except queue.Empty:
            pass
    raise TimeoutError(f"Timeout waiting for '{text}'")

def analyze_fen(fen, depth=15):
    global stockfish_process
    if not stockfish_process:
        raise RuntimeError("Stockfish process is not running")

    send_command(f"position fen {fen}")
    send_command(f"go depth {depth}")

    best_move = None
    eval_score = None

    start = time.time()
    while time.time() - start < 10:
        try:
            line = output_queue.get(timeout=0.1)
            if "info depth" in line and "score" in line:
                if "cp" in line:
                    eval_score = int(line.split("cp")[1].split()[0]) / 100
                elif "mate" in line:
                    eval_score = f"mate {line.split('mate')[1].split()[0]}"
            if "bestmove" in line:
                best_move = line.split("bestmove")[1].split()[0]
                break
        except queue.Empty:
            continue

    return {"score": eval_score, "best_move": best_move or "none"}


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
    player = data["player"]
    date = data["date"]
    filename = data["filename"]

    game_path = os.path.join(GAMES_DIR, player, date, filename)

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

@main.route("/start_stockfish")
def start_stockfish():
    global stockfish_process
    if stockfish_process is None or stockfish_process.poll() is not None:
        import subprocess
        stockfish_process = subprocess.Popen(
            ["/usr/games/stockfish"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return {"status": "Stockfish started"}
    return {"status": "Stockfish already running"}

@main.route("/stop_stockfish")
def stop_stockfish():
    global stockfish_process
    print("Received stop_stockfish request")
    if stockfish_process and stockfish_process.poll() is None:
        print("Terminating Stockfish process...")
        stockfish_process.kill()
        stockfish_process = None
        print("Stockfish stopped.")
        return {"status": "Stockfish stopped"}
    print("Stockfish process not running.")
    return {"status": "Stockfish not running"}


@main.route("/analyze_fen", methods=["POST"])
def analyze_fen_route():
    data = request.get_json()
    fen = data.get("fen")
    if not fen:
        return jsonify({"error": "Missing FEN"}), 400
    
    stockfish.set_fen_position(fen)
    info = stockfish.get_evaluation()
    best_move = stockfish.get_best_move()
    return jsonify({
        "score": info.get("value"),
        "type": info.get("type"),
        "best_move": best_move
    })

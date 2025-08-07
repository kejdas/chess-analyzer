import subprocess
import os

from dotenv import load_dotenv
load_dotenv()

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")

def analyze_with_stockfish(fen, depth=15, timeout=10):
    """
    Analyze a position with Stockfish and return evaluation and best move.
    Returns: dict with 'score', 'best_move', or 'error'.
    """
    try:
        with subprocess.Popen(
            [STOCKFISH_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        ) as process:
            process.stdin.write("uci\nisready\n")
            process.stdin.flush()
            # Wait for readyok with timeout
            for _ in range(timeout * 10):
                line = process.stdout.readline()
                if "readyok" in line:
                    break

            process.stdin.write(f"position fen {fen}\n")
            process.stdin.write(f"go depth {depth}\n")
            process.stdin.flush()

            output = ""
            best_move = None
            eval_score = None

            # Read output with timeout
            import time
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    return {"error": "Stockfish analysis timed out"}
                line = process.stdout.readline()
                if not line:
                    break
                output += line
                if "info depth" in line and "score" in line:
                    if "cp" in line:
                        try:
                            eval_score = int(line.split("cp")[1].split()[0]) / 100
                        except Exception:
                            pass
                    elif "mate" in line:
                        try:
                            eval_score = f"mate {line.split('mate')[1].split()[0]}"
                        except Exception:
                            pass
                if "bestmove" in line:
                    try:
                        best_move = line.split("bestmove")[1].strip().split()[0]
                    except Exception:
                        best_move = None
                    break

            return {
                "score": eval_score,
                "best_move": best_move
            }
    except Exception as e:
        return {"error": str(e)}1

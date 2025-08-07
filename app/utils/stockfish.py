import subprocess

STOCKFISH_PATH = "/usr/games/stockfish"


def analyze_with_stockfish(fen, depth=15):
    global stockfish_process
    if stockfish_process is None:
        return {"error": "Stockfish is not running"}

    # Wyślij polecenia do Stockfish
    stockfish_process.stdin.write(f"position fen {fen}\n")
    stockfish_process.stdin.write(f"go depth {depth}\n")
    stockfish_process.stdin.flush()

    output = ""
    while True:
        line = stockfish_process.stdout.readline()
        if not line:
            break
        output += line
        if "bestmove" in line:
            break

    # Parsowanie wyniku
    best_move = None
    eval_score = None

    for line in output.splitlines():
        if "info depth" in line and "score" in line:
            if "cp" in line:
                eval_score = int(line.split("cp")[1].split()[0]) / 100
            elif "mate" in line:
                eval_score = f"mate {line.split('mate')[1].split()[0]}"
        if "bestmove" in line:
            best_move = line.split("bestmove")[1].strip().split()[0]

    return {
        "score": eval_score,
        "best_move": best_move
    }


    except Exception as e:
        # Ensure process is terminated if an error occurs
        try:
            process.kill()
        except Exception:
            pass
        return {"error": str(e)}


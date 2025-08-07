import subprocess

STOCKFISH_PATH = "/usr/games/stockfish"

def analyze_with_stockfish(fen, depth=15):
    try:
        process = subprocess.Popen(
            [STOCKFISH_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )
        process.stdin.write("uci\n")
        process.stdin.write("isready\n")
        process.stdin.flush()
        # Wait for readyok
        while True:
            line = process.stdout.readline()
            if "readyok" in line:
                break

        process.stdin.write(f"position fen {fen}\n")
        process.stdin.write(f"go depth {depth}\n")
        process.stdin.flush()

        output = ""
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output += line
            if "bestmove" in line:
                break

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

        process.terminate()
        return {
            "score": eval_score,
            "best_move": best_move
        }
    except Exception as e:
        try:
            process.kill()
        except Exception:
            pass
        return {"error": str(e)}

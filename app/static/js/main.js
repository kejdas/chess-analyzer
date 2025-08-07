let board = null;
let game = null;
let moves = [];
let moveIndex = 0;
let capturedWhite = [];
let capturedBlack = [];
let prevEval = null;
let blunders = { w: 0, b: 0 };
let inaccuracies = { w: 0, b: 0 };
let moveAcc = { w: [], b: [] };

function pieceUnicode(piece) {
  const map = {
    p: "♟", n: "♞", b: "♝", r: "♜", q: "♛", k: "♚",
    P: "♙", N: "♘", B: "♗", R: "♖", Q: "♕", K: "♔"
  };
  return map[piece] || "";
}

function updateCaptured() {
  // Reset
  capturedWhite = [];
  capturedBlack = [];
  let tempGame = new Chess();
  for (let i = 0; i < moveIndex; i++) {
    let move = tempGame.move(moves[i].move, { sloppy: true });
    if (move.captured) {
      if (move.color === "w") capturedWhite.push(pieceUnicode(move.captured));
      else capturedBlack.push(pieceUnicode(move.captured.toUpperCase()));
    }
  }
  document.getElementById("white-captured").innerText = capturedWhite.join(" ");
  document.getElementById("black-captured").innerText = capturedBlack.join(" ");
}

function updateTurnIndicator() {
  const turn = game.turn() === "w" ? "White to move" : "Black to move";
  document.getElementById("turn-indicator").innerText = turn;
}

function updateEvalBar(score) {
  // score: centipawns, positive = white, negative = black, 0 = equal
  // Clamp score to [-10, 10] for bar
  let percent = 50;
  if (typeof score === "number") {
    percent = Math.max(0, Math.min(100, 50 + score * 5));
  } else if (typeof score === "string" && score.startsWith("mate")) {
    percent = score.includes("-") ? 0 : 100;
  }
  const bar = document.getElementById("eval-bar");
  bar.style.height = percent + "%";
  bar.style.bottom = (100 - percent) + "%";
}

function updateAccuracyTable() {
  document.getElementById("white-blunders").innerText = blunders.w;
  document.getElementById("black-blunders").innerText = blunders.b;
  document.getElementById("white-inacc").innerText = inaccuracies.w;
  document.getElementById("black-inacc").innerText = inaccuracies.b;
  document.getElementById("white-acc").innerText = moveAcc.w.length
    ? ((moveAcc.w.reduce((a, b) => a + b, 0) / moveAcc.w.length) * 100).toFixed(1)
    : "-";
  document.getElementById("black-acc").innerText = moveAcc.b.length
    ? ((moveAcc.b.reduce((a, b) => a + b, 0) / moveAcc.b.length) * 100).toFixed(1)
    : "-";
}

function loadGame(player, date, filename) {
  fetch("/load_game", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player, date, filename }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        document.getElementById("info").innerText = "Failed to load game: " + data.error;
        return;
      }
      // Expecting: { moves: [...], white: "...", black: "...", opening: { name: "...", url: "..." } }
      moves = data.moves || data;
      game = new Chess();
      moveIndex = 0;
      blunders = { w: 0, b: 0 };
      inaccuracies = { w: 0, b: 0 };
      moveAcc = { w: [], b: [] };
      prevEval = null;
      board.position(game.fen());

      // Player nicknames
      document.getElementById("white-nick").innerText = data.white || "White";
      document.getElementById("black-nick").innerText = data.black || "Black";
      document.getElementById("white-nick-acc").innerText = data.white || "White";
      document.getElementById("black-nick-acc").innerText = data.black || "Black";

      // Opening info
      if (data.opening && data.opening.name) {
        document.getElementById("opening-name").innerText = data.opening.name;
        if (data.opening.url) {
          const link = document.getElementById("opening-link");
          link.href = data.opening.url;
          link.style.display = "";
        }
      }

      updateInfo();
    })
    .catch((err) => {
      console.error("Failed to load game:", err);
      document.getElementById("info").innerText = "Failed to load game.";
    });
}

function nextMove() {
  if (moveIndex < moves.length) {
    game.move(moves[moveIndex].move);
    moveIndex++;
    board.position(game.fen());
    updateInfo();
  }
}

function prevMove() {
  if (moveIndex > 0) {
    game.undo();
    moveIndex--;
    board.position(game.fen());
    updateInfo();
  }
}

function updateInfo() {
  const info = document.getElementById("info");
  const fen = game.fen();
  info.innerText = `Move ${moveIndex}/${moves.length}`;
  updateTurnIndicator();
  updateCaptured();

  fetch("/analyze_fen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fen: fen }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        info.innerText += " | Evaluation unavailable.";
        updateEvalBar(0);
      } else {
        info.innerText += ` | Eval: ${data.score} | Best move: ${data.best_move}`;
        updateEvalBar(data.score);

        // Blunder/inaccuracy tracking (simple example, adjust thresholds as needed)
        if (prevEval !== null && typeof data.score === "number") {
          const diff = Math.abs(data.score - prevEval);
          const color = game.turn() === "w" ? "b" : "w"; // last move's color
          if (diff > 2) blunders[color]++;
          else if (diff > 1) inaccuracies[color]++;
          moveAcc[color].push(Math.max(0, 1 - diff / 5)); // crude accuracy
        }
        prevEval = typeof data.score === "number" ? data.score : prevEval;
        updateAccuracyTable();
      }
    })
    .catch((err) => {
      console.error("Stockfish error:", err);
      info.innerText += " | Evaluation unavailable.";
      updateEvalBar(0);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  board = Chessboard("board", { position: "start", pieceTheme: "/static/img/chesspieces/wikipedia/{piece}.png" });
  game = new Chess();

  document.getElementById("prevBtn").addEventListener("click", prevMove);
  document.getElementById("nextBtn").addEventListener("click", nextMove);

  const urlParams = new URLSearchParams(window.location.search);
  const player = urlParams.get("player");
  const date = urlParams.get("date");
  const file = urlParams.get("file");

  if (player && date && file) {
    loadGame(player, date, file);
  }
});

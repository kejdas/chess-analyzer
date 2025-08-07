let board = null;
let game = null;
let moves = [];
let moveIndex = 0;

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
      moves = data;
      game = new Chess();
      moveIndex = 0;
      board.position(game.fen());
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
  fetch("/analyze_fen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fen: fen }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        info.innerText += " | Evaluation unavailable.";
      } else {
        info.innerText += ` | Eval: ${data.score} | Best move: ${data.best_move}`;
      }
    })
    .catch((err) => {
      console.error("Stockfish error:", err);
      info.innerText += " | Evaluation unavailable.";
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

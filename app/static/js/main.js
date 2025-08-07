let board = null;
let game = null;
let moves = [];
let moveIndex = 0;

// Funkcja ładująca grę (tak jak masz)
function loadGame(player, date, filename) {
  fetch("/load_game", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player, date, filename }),
  })
    .then((res) => res.json())
    .then((data) => {
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

// Funkcja do przesuwania się o ruch do przodu
function nextMove() {
  if (moveIndex < moves.length) {
    game.move(moves[moveIndex].move);
    moveIndex++;
    board.position(game.fen());
    updateInfo();
  }
}

// Funkcja do cofania ruchu
function prevMove() {
  if (moveIndex > 0) {
    game.undo();
    moveIndex--;
    board.position(game.fen());
    updateInfo();
  }
}

// Aktualizacja informacji o ruchu
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
      info.innerText += ` | Eval: ${data.score} | Best move: ${data.best_move}`;
    })
    .catch((err) => {
      console.error("Stockfish error:", err);
      info.innerText += " | Evaluation unavailable.";
    });
}


// Inicjalizacja i podpięcie event listenerów
document.addEventListener("DOMContentLoaded", () => {
  board = Chessboard("board", { position: "start", pieceTheme: "/static/img/chesspieces/wikipedia/{piece}.png" });

  document.getElementById("prevBtn").addEventListener("click", prevMove);
  document.getElementById("nextBtn").addEventListener("click", nextMove);

  const urlParams = new URLSearchParams(window.location.search);
  const player = urlParams.get("player");
  const date = urlParams.get("date");
  const file = urlParams.get("file");

  if (player && date && file) {
    loadGame(player, date, file);
  }

  // START Stockfish po wejściu na stronę viewer
  fetch("/start_stockfish")
    .then(res => res.json())
    .then(data => console.log("Stockfish started:", data))
    .catch(err => console.error("Failed to start Stockfish:", err));
});

// STOP Stockfish przy opuszczaniu strony (zamknięcie/odświeżenie/przejście)
window.addEventListener("beforeunload", () => {
  if (navigator.sendBeacon) {
    navigator.sendBeacon("/stop_stockfish", "");
  } else {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/stop_stockfish", false);  // synchroniczny request, by miał szansę wykonać się przed zamknięciem
    xhr.send();
  }
});


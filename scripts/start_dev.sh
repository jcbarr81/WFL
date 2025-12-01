#!/usr/bin/env bash
set -euo pipefail

# Starts backend and frontend; tries terminal windows, falls back to background.
# Backend: Django runserver on 8000
# Frontend: Vite dev server on 3000
# Use FORCE_BACKGROUND=1 to skip terminal launch.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

pick_terminal() {
  if [[ -n "${FORCE_BACKGROUND:-}" ]]; then
    return 1
  fi
  if [[ -n "${TERMINAL_CMD:-}" ]]; then
    echo "$TERMINAL_CMD"
    return 0
  fi
  for cmd in gnome-terminal xfce4-terminal konsole mate-terminal xterm; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "$cmd"
      return 0
    fi
  done
  return 1
}

launch_terminal() {
  local term="$1"
  local title="$2"
  shift 2
  local cmd="$*; exec bash"
  case "$term" in
    gnome-terminal) gnome-terminal --title="$title" -- bash -lc "$cmd" ;;
    xfce4-terminal) xfce4-terminal --title="$title" --command="bash -lc '$cmd'" ;;
    konsole) konsole --title "$title" -e bash -lc "$cmd" ;;
    mate-terminal) mate-terminal --title "$title" --command="bash -lc '$cmd'" ;;
    xterm) xterm -T "$title" -e bash -lc "$cmd" ;;
    *) return 1 ;;
  esac
}

launch_background() {
  local title="$1"
  shift
  local cmd="$*"
  local log_dir="$ROOT_DIR/.logs"
  mkdir -p "$log_dir"
  local logfile="$log_dir/${title// /_}.log"
  echo "Starting $title in background (logs: $logfile)"
  nohup bash -lc "$cmd" >"$logfile" 2>&1 &
  echo "$!" >"$logfile.pid"
}

echo "Stopping any existing dev servers on ports 8000/3000..."
lsof -ti :8000 2>/dev/null | xargs -r kill || true
lsof -ti :3000 2>/dev/null | xargs -r kill || true

backend_cmd="cd \"$ROOT_DIR/backend\" && source ../.venv/bin/activate && python manage.py runserver 0.0.0.0:8000"
frontend_cmd="cd \"$ROOT_DIR/frontend\" && npm run dev -- --host 0.0.0.0 --port 3000"

TERMINAL=$(pick_terminal || true)
if [[ -n "$TERMINAL" ]]; then
  echo "Launching backend in $TERMINAL..."
  if ! launch_terminal "$TERMINAL" "WFL Backend" "$backend_cmd"; then
    echo "Terminal launch failed; running backend in background." >&2
    launch_background "backend" "$backend_cmd"
  fi

  echo "Launching frontend in $TERMINAL..."
  if ! launch_terminal "$TERMINAL" "WFL Frontend" "$frontend_cmd"; then
    echo "Terminal launch failed; running frontend in background." >&2
    launch_background "frontend" "$frontend_cmd"
  fi
  echo "Done. If windows did not appear, check .logs/ for output."
else
  echo "No supported terminal launcher found; starting in background."
  launch_background "backend" "$backend_cmd"
  launch_background "frontend" "$frontend_cmd"
  echo "Servers running in background. Tail logs with: tail -f .logs/backend.log .logs/frontend.log"
fi

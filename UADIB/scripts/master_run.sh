#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PORT="${UADIB_PORT:-8080}"
START_SIMULATOR="${UADIB_START_SIMULATOR:-1}"
SIM_ENDPOINT="${UADIB_SIM_ENDPOINT:-mavlink://udp:127.0.0.1:14550}"
MAX_PORT_SCAN="${UADIB_MAX_PORT_SCAN:-20}"

log() {
  printf '[UADIB] %s\n' "$*" >&2
}

kill_uadib_processes() {
  log "Stopping existing UADIB-related processes (if any)..."

  # Kill only processes related to this workspace/project.
  pkill -f "uvicorn api.server:app" 2>/dev/null || true
  pkill -f "python -m simulator.mock_drone" 2>/dev/null || true

  sleep 1
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

kill_processes_on_port() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi

  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  log "Port $port is in use; stopping process(es): $pids"
  kill $pids 2>/dev/null || true
  sleep 1

  if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    log "Force stopping process(es) on port $port"
    kill -9 $pids 2>/dev/null || true
    sleep 1
  fi
}

resolve_server_port() {
  local requested_port="$1"
  local port="$requested_port"
  local i=0

  kill_processes_on_port "$port"
  if ! port_in_use "$port"; then
    echo "$port"
    return 0
  fi

  while (( i < MAX_PORT_SCAN )); do
    port=$((requested_port + i + 1))
    if ! port_in_use "$port"; then
      log "Requested port $requested_port is busy; using next available port $port"
      echo "$port"
      return 0
    fi
    i=$((i + 1))
  done

  log "Unable to find a free port in range ${requested_port}..$((requested_port + MAX_PORT_SCAN))"
  exit 1
}

setup_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    log "Using existing virtual environment at $VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  log "Upgrading pip and installing dependencies"
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -e .[dev]
}

start_system() {
  export UADIB_AUTH_TOKEN="${UADIB_AUTH_TOKEN:-changeme}"

  local sim_pid=""
  if [[ "$START_SIMULATOR" == "1" ]]; then
    log "Starting mock simulator: $SIM_ENDPOINT"
    python -m simulator.mock_drone --endpoint "$SIM_ENDPOINT" > /tmp/uadib-simulator.log 2>&1 &
    sim_pid="$!"
    log "Simulator PID: $sim_pid (log: /tmp/uadib-simulator.log)"
  fi

  cleanup() {
    log "Shutting down UADIB processes..."
    if [[ -n "$sim_pid" ]]; then
      kill "$sim_pid" 2>/dev/null || true
    fi
    pkill -f "uvicorn api.server:app" 2>/dev/null || true
  }

  trap cleanup EXIT INT TERM

  local server_port
  server_port="$(resolve_server_port "$PORT")"
  export UADIB_PORT="$server_port"
  log "Starting API server on http://127.0.0.1:${server_port}"
  exec uvicorn api.server:app --host 0.0.0.0 --port "$server_port"
}

kill_uadib_processes
setup_venv
start_system

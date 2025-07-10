#!/usr/bin/env bash
# refreshsetup.sh – One-stop script for the OPC UA / MODBUS PLC Emulator
# ---------------------------------------------------------------
set -euo pipefail

# ------------- helper --------------------------------------------------------
usage() {
  cat <<'EOF'
OPC UA MODBUS PLC Emulator
=========================
Usage: ./refreshsetup.sh <command> [<command> …]

Commands (you can chain several in one line):
  build        Build all Docker images
  up           Start services (opcua-server) and warm-up
  down         Stop services
  restart      Restart services
  logs         Tail logs for all services
  server-logs  Tail only server logs
  scanner-logs Tail only scanner logs
  scan         Run the OPC-UA scanner once
  status       Show docker-compose service status
  clean        Remove containers, volumes, dangling images
  test         Quick TCP connection test to port 4840
  monitor      Continuous scanner run (Ctrl+C to stop)
  help         Show this help

Hints
-----
• Chain commands: ./refreshsetup.sh clean build up
• Uses 'docker compose' if available, else falls back to 'docker-compose'.
EOF
}

# Pick Compose v2 if present, else v1
compose() {
  if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    docker compose "$@"
  elif command -v docker-compose &>/dev/null; then
    docker-compose "$@"
  else
    echo "❌ Neither 'docker compose' nor 'docker-compose' found in PATH." >&2
    exit 1
  fi
}

# Small helpers
separator() { printf '\n%s\n' "---------------------------------------------------------------"; }

wait_for_server() {
  echo "⏳ Waiting for server to start (5 s)…"
  sleep 5
  echo "✅ Server should be ready. Run './refreshsetup.sh scan' to test."
}

# ------------- commands ------------------------------------------------------
cmd_build()        { separator; echo "🔨 Building Docker images…"; compose build; }
cmd_up()           { separator; echo "🚀 Starting OPC UA services…"; compose up -d opcua-server; wait_for_server; }
cmd_down()         { separator; echo "🛑 Stopping services…"; compose down; }
cmd_restart()      { separator; echo "♻️  Restarting services…"; compose restart; }
cmd_logs()         { separator; echo "📜 Tailing logs (Ctrl+C to exit)…"; compose logs -f; }
cmd_server_logs()  { separator; echo "📜 Server logs (Ctrl+C to exit)…"; compose logs -f opcua-server; }
cmd_scanner_logs() { separator; echo "📜 Scanner logs (Ctrl+C to exit)…"; compose logs -f opcua-scanner; }
cmd_scan()         { separator; echo "🔍 Running one-time scanner…"; compose run --rm opcua-scanner; }
cmd_status()       { separator; echo "📋 Service status:"; compose ps; }
cmd_clean() {
  separator
  echo "🧹 Cleaning containers & volumes…"
  compose down -v
  compose rm -f || true
  docker system prune -f
}
cmd_test() {
  separator
  echo "🔗 Testing OPC UA TCP connection…"
  compose exec opcua-server python - <<'PY'
import socket, sys, time
host, port = "localhost", 4840
s = socket.socket(); s.settimeout(3)
try:
    s.connect((host, port)); s.close()
    print("✅ Server is responsive on %s:%d" % (host, port))
except Exception as e:
    print("❌ Connection failed:", e); sys.exit(1)
PY
}
cmd_monitor()      { separator; echo "🖥️  Continuous monitoring (Ctrl+C to stop)…"; compose run --rm opcua-scanner python opcua_scanner.py; }
cmd_help()         { usage; }

# ------------- dispatcher ----------------------------------------------------
# If no args, show help
[[ $# -eq 0 ]] && { usage; exit 0; }

for cmd in "$@"; do
  case $cmd in
    build)        cmd_build        ;;
    up)           cmd_up           ;;
    down)         cmd_down         ;;
    restart)      cmd_restart      ;;
    logs)         cmd_logs         ;;
    server-logs)  cmd_server_logs  ;;
    scanner-logs) cmd_scanner_logs ;;
    scan)         cmd_scan         ;;
    status)       cmd_status       ;;
    clean)        cmd_clean        ;;
    test)         cmd_test         ;;
    monitor)      cmd_monitor      ;;
    help|-h|--help) cmd_help && exit 0 ;;
    *) echo "Unknown command: '$cmd'"; usage; exit 1 ;;
  esac
done

#!/usr/bin/env bash
# refresh_setup.sh - Build and run the OPC UA emulator and scanner
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./refresh_setup.sh [-b] [-s <service>] [-h]

Options:
  -b            Build Docker images
  -s <service>  Start service: opc_emulator, scanner, or all
  -h            Show this help

Examples:
  ./refresh_setup.sh -b -s opc_emulator  # build images and start the emulator
  ./refresh_setup.sh -s scanner          # run the scanner once
USAGE
}

# choose docker compose v2 or v1
compose() {
  if command -v docker &>/dev/null && docker compose version &>/dev/null; then
    docker compose "$@"
  elif command -v docker-compose &>/dev/null; then
    docker-compose "$@"
  else
    echo "Neither docker compose nor docker-compose found" >&2
    exit 1
  fi
}

build=false
service=""

while getopts ":bs:h" opt; do
  case "$opt" in
    b) build=true ;;
    s) service="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac
done

$build && compose build

case "$service" in
  opc_emulator)
    compose up -d opcua-server
    ;;
  scanner)
    compose run --rm opcua-scanner
    ;;
  all)
    compose up -d
    ;;
  "")
    ;; # nothing to start
  *)
    echo "Unknown service: $service" >&2
    usage
    exit 1
    ;;
esac

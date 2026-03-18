#!/bin/sh
# Optional script for custom liveness/readiness probes (exec). Plugin-only check, no UFM dependency.
# Requires /bin/sh in the plugin image. For default liveness, the chart uses native httpGet/tcpSocket probes instead.
set -e

check_http() {
  URL="$1"; T="${2:-5}"
  command -v curl >/dev/null 2>&1 && curl -sf --max-time "$T" "$URL" >/dev/null 2>&1 && return 0
  command -v wget >/dev/null 2>&1 && wget -q -O /dev/null --timeout="$T" "$URL" 2>/dev/null && return 0
  command -v python3 >/dev/null 2>&1 && python3 -c "import urllib.request,socket;socket.setdefaulttimeout($T);urllib.request.urlopen('$URL')" 2>/dev/null && return 0
  return 1
}

check_tcp() {
  H="$1"; P="$2"; T="${3:-5}"
  command -v nc >/dev/null 2>&1 && nc -z -w "$T" "$H" "$P" 2>/dev/null && return 0
  command -v python3 >/dev/null 2>&1 && python3 -c "import socket;s=socket.socket();s.settimeout($T);s.connect(('$H',$P));s.close()" 2>/dev/null && return 0
  return 1
}

if [ -n "$HEALTH_ENDPOINT" ]; then
  HEALTH_PORT="${HEALTH_PORT:-$PLUGIN_PORT}"
  PLUGIN_URL="http://127.0.0.1:${HEALTH_PORT}${HEALTH_ENDPOINT}"
  check_http "$PLUGIN_URL" 5 || { echo "ERROR: Plugin health endpoint not responding" >&2; exit 1; }
elif [ -n "$PLUGIN_PORT" ]; then
  check_tcp "127.0.0.1" "$PLUGIN_PORT" 5 || { echo "ERROR: Plugin port not responding" >&2; exit 1; }
fi
exit 0

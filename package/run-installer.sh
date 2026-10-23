#!/usr/bin/env bash
# Keep graphical launches visible and capture the real installer's exit status.
set -euo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:?install or uninstall is required}"
shift
case "$ACTION" in install|uninstall) ;; *) exit 2 ;; esac
DESKTOP=0
if [[ "${1:-}" == --desktop ]]; then DESKTOP=1; shift; fi

# Dolphin can run a shell script without a terminal. Never hide sudo prompts,
# app-loader confirmation, build progress or a failure in that case.
if [[ ! -t 0 || ! -t 1 ]] && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && [[ "${VITALUX_THEME_TERMINAL:-0}" != 1 ]]; then
    export VITALUX_THEME_TERMINAL=1
    if command -v konsole >/dev/null 2>&1; then
        exec konsole --separate --hold -e bash "$BASE/run-installer.sh" "$ACTION" "$@"
    elif command -v xdg-terminal-exec >/dev/null 2>&1; then
        exec xdg-terminal-exec bash "$BASE/run-installer.sh" "$ACTION" --desktop "$@"
    fi
    MESSAGE='Kein Terminal gefunden. Bitte Konsole öffnen und im entpackten Theme-Ordner bash install.sh bzw. bash uninstall.sh ausführen.'
    if command -v kdialog >/dev/null 2>&1; then kdialog --error "$MESSAGE"; fi
    printf '%s\n' "$MESSAGE" >&2
    exit 1
fi

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/liquid-glass-kde"
LOG_FILE="$LOG_DIR/$ACTION.log"
(umask 077; mkdir -p -- "$LOG_DIR"; touch -- "$LOG_FILE")
chmod 600 -- "$LOG_FILE"
cd -- "$BASE"
printf '\n=== Vitalux Liquid Silver · %s · %s ===\nProtokoll: %s\n' "$ACTION" "$(date -Is)" "$LOG_FILE" | tee -a "$LOG_FILE"
RESULT=0
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3 fehlt. Auf openSUSE: sudo zypper install python3' | tee -a "$LOG_FILE" >&2
    RESULT=1
else
    set +e
    python3 -u tools/full_install.py "$ACTION" "$@" 2>&1 | tee -a "$LOG_FILE"
    RESULTS=("${PIPESTATUS[@]}")
    set -e
    RESULT="${RESULTS[0]}"
    if [[ "$RESULT" == 0 && "${RESULTS[1]}" != 0 ]]; then RESULT="${RESULTS[1]}"; fi
fi
printf '\nBeendet mit Status %s. Protokoll: %s\n' "$RESULT" "$LOG_FILE"
if [[ "$DESKTOP" == 1 && -t 0 ]]; then
    read -r -p 'Zum Schließen Eingabetaste drücken … ' _ || true
fi
exit "$RESULT"

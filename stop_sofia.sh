#!/bin/bash
# 🛑 Script para detener la sesión tmux de Sofía

SESSION_NAME="sofia"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "🛑 Deteniendo Sofía..."
    tmux kill-session -t $SESSION_NAME
    echo "✅ Sofía ha sido detenida correctamente."
else
    echo "⚠️ No hay ninguna sesión de Sofía activa."
fi

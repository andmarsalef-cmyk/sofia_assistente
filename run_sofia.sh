#!/bin/bash
# 🚀 Script para lanzar Sofía en segundo plano con tmux

SESSION_NAME="sofia"

# Verificar si la sesión ya está corriendo
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "✅ Sofía ya está corriendo. Conéctate con: tmux attach -t $SESSION_NAME"
    exit 0
fi

# Crear nueva sesión y lanzar el bot
echo "🚀 Iniciando Sofía..."
tmux new-session -d -s $SESSION_NAME "source venv/bin/activate && python sofia_telegram.py"
echo "✅ Sofía está corriendo en tmux. Usa: tmux attach -t $SESSION_NAME para verla."


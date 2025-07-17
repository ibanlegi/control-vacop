# source back_setup.sh

#!/bin/bash

echo "Enabling CAN interface (can0)..."

sudo ip link set can0 up type can bitrate 1000000

if [ $? -eq 0 ]; then
    echo "CAN interface 'can0' enabled successfully (1 Mbit/s)"
else
    echo "Failed to enable CAN interface"
    exit 1
fi

echo ""
echo "Activating Python virtual environment..."

VENV_PATH="../../solopy-env/bin/activate"

if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
    echo "Virtual environment activated from $VENV_PATH"
else
    echo "Virtual environment not found at $VENV_PATH"
    exit 1
fi

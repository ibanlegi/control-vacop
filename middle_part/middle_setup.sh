# chmod +x middle_setup.sh

# ./middle_setup.sh

#!/bin/bash

echo "Enabling CAN interface (can0)..."

sudo ip link set can0 up type can bitrate 1000000

if [ $? -eq 0 ]; then
    echo "CAN interface 'can0' enabled successfully (1 Mbit/s)"
else
    echo "Failed to enable CAN interface"
    exit 1
fi

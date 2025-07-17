# File: AcceleratorManager.py
# This file is part of the VACOP project.
# Created by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import time
import Adafruit_MCP3008

from CAN_system.CANSystem import CANSystem


ACCEL_THRESHOLD = 0


class AcceleratorManager:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.mcp = Adafruit_MCP3008.MCP3008(clk=21, cs=7, miso=19, mosi=20)
        self.can_system = CANSystem(verbose=self.verbose, device_name='BRAKE')
        #self.can_system.set_callback(self.read_accelerator)
        self.lastAccelPedal = None
        self.on_init()

    def __del__(self):
        self._print("Quitting AcceleratorManager...")

    def on_init(self):
        running = False
        self._print("Waiting for start command from OBU...\n")

        # Wait for the "start" CAN message
        while not running:
            can_msg = self.can_system.listener.can_input()
            if can_msg is not None:
                self._print("Received CAN message:", can_msg)

                if isinstance(can_msg, tuple) and len(can_msg) >= 3:
                    _, order_id, _ = can_msg

                    if order_id == "start":
                        running = True

            time.sleep(0.1)  # To avoid busy waiting

        self._print("Initializing system...\n")

        self.can_system.can_send("OBU", "brake_rdy")
        time.sleep(0.2)
        self.can_system.can_send("OBU", "brake_rdy")
        self.can_system.can_send("OBU", "brake_rdy")

        self._print("System initialized. Listening for further commands...\n")
    
        while True:
            self.read_accelerator()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def read_accelerator(self):
        # This function is called back on CAN message reception
        # We'll read the accelerator sensor value and send it on CAN if it changed enough

        accelPedal = int(self.mcp.read_adc(0))
        self._print(f"Raw accelerator value: {accelPedal}")

        # Clamp accelerator value
        accelPedal = max(250, min(accelPedal, 875))

        # Map from [250, 875] to [0, 1023]
        mapped_value = int(((accelPedal - 250) / (875 - 250)) * 1023)
        self._print(f"Mapped accelerator value: {mapped_value}")

        # Check if change exceeds threshold
        if self.lastAccelPedal is None or abs(mapped_value - self.lastAccelPedal) > ACCEL_THRESHOLD:
            self.lastAccelPedal = mapped_value
            self.can_system.can_send("OBU", "accel_pedal", mapped_value)
        


if __name__ == "__main__":
    try:
        manager = AcceleratorManager(verbose=True)
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")

# File: OBU.py
# This file is part of the VACOP project.
# Created by Rémi Myard
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License

# Execute : python3 -m back_part.OBU -v


from CAN_system.CANSystem import CANSystem
import argparse
import time

MAX_TORQUE = 20.0
TORQUE_SCALE = MAX_TORQUE / 1023.0


class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.canSystem = CANSystem(verbose=self.verbose, device_name='OBU')

        self.canSystem.set_callback(self.on_can_message)
        self.canSystem.start_listening()
    
    def on_can_message(self, _, messageType, data):
        """Callback function"""
        print(f"[CALLBACK] {messageType}, data: {data}")
        match messageType:
            case "brake_rdy" | "steer_rdy":
                print("rdy")
            case "accel_pedal":
                self._on_set_torque(data)
            case "brake_enable":
                self._on_ending()
            case "bouton_park":
                self._event_park_btn()
            case "bouton_auto_manu":
                print("Auto/Manu Button Detection: Not implemented")
            case "bouton_on_off":
                print("On/Off Button Detection: Not implemented")
            case "bouton_reverse":
                print("Reverse Button Detection: Not implemented")
            case _:
                self._handle_event(messageType, data)
    
    def _event_park_btn(self):
        print("Park Button Detection: Not implemented")
    

    def _on_set_torque(self, data):
        try:
            torque_value = float(data) * TORQUE_SCALE
            print("New torque = ", torque_value)
        except Exception:
            print(f"ERROR: Invalid torque data: {data}")

    def _handle_event(self, messageType, data):
        print(f"[Unhandled] {messageType}, data: {data}")

    def _on_ending(self):
        print("Shutting down...")
        self.canSystem.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OBU system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    obu = OBU(verbose=args.verbose)
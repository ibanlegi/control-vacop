# File: OBU.py
# This file is part of the VACOP project.
# Created by Rémi Myard
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License

# Execute : python3 -m back_part.OBU -v


from CAN_system.CANSystem import CANSystem
from .DualMotorController import DualMotorController
import argparse
import time

MAX_TORQUE = 20.0
TORQUE_SCALE = MAX_TORQUE / 1023.0


class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.motors = DualMotorController(verbose=self.verbose)
        self.canSystem = CANSystem(verbose=self.verbose, device_name='OBU')
        self.readyComponents = set()
        self.mode = None
        self.state = None

        self.canSystem.set_callback(self.on_can_message)
        self._change_mode("INITIALIZE")
    
    def on_can_message(self, _, messageType, data):
        """Callback function"""
        match messageType:
            case "brake_rdy" | "steer_rdy":
                self._on_rdy(messageType)
            case "accel_pedal":
                self._on_set_torque(data)
            case "brake_enable":
                self._on_ending()
            case "bouton_park":
                print("Park Button Detection: Not implemented")
            case "bouton_auto_manu":
                print("Auto/Manu Button Detection: Not implemented")
            case "bouton_on_off":
                print("On/Off Button Detection: Not implemented")
            case "bouton_reverse":
                print("Reverse Button Detection: Not implemented")
            case _:
                self._handle_event(messageType, data)

    def _change_mode(self, newMode):
        self.mode = newMode
        match self.mode:
            case "INITIALIZE":
                #self.canSystem.can_send("BRAKE", "start", 0)
                self.canSystem.can_send("STEER", "start", 0)
                time.sleep(0.5)
                print("INIT")
                self.canSystem.start_listening()
            case "START":
                self._change_mode("MANUAL")
            case "MANUAL":
                self._change_state("FORWARD")
                self.canSystem.can_send("STEER", "steer_enable", False)
            case "AUTO":
                print("AUTO mode not implemented.")
                self.canSystem.can_send("STEER", "steer_enable", True)
                time.sleep(5)
                print("send value steer")
                self.canSystem.can_send("STEER", "steer_pos_set", 700)
                time.sleep(10)
                print("send value steer")
                self.canSystem.can_send("STEER", "steer_pos_set", 350)
            case "ERROR":
                self._change_mode("INITIALIZE")
            case "OFF":
                self._on_ending()
            case _:
                print(f"Unknown mode '{self.mode}'")
                self._change_mode("OFF")

    def _change_state(self, newState):
        self.state = newState
        match self.state:
            case "FORWARD":
                self.motors.set_forward()
                print("Direction : FORWARD")
            case "REVERSE":
                self.motors.set_reverse()
                print("Direction : REVERSE")
            case "ERROR":
                self._change_mode("ERROR")

    def _on_rdy(self, msgType):
        if self.mode == "INITIALIZE" and msgType not in self.readyComponents:
            self.readyComponents.add(msgType)
            if len(self.readyComponents) > 0:
                self._change_mode("START")

    def _on_set_torque(self, data):
        if self.mode not in {"MANUAL", "AUTO"}:
            print(f"ERROR: Cannot set torque in mode '{self.mode}'")
            return
        try:
            torque_value = float(data) * TORQUE_SCALE
            self.motors.set_torque(torque_value)
            print("New torque = ", torque_value)
        except Exception:
            print(f"ERROR: Invalid torque data: {data}")

    def _handle_event(self, messageType, data):
        print(f"[Unhandled] {messageType}, data: {data}, state: {self.state}")

    def _on_ending(self):
        print("Shutting down...")
        #self.canSystem.can_send("BRAKE", "stop", 0)
        self.canSystem.can_send("STEER", "stop", 0)
        self.canSystem.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OBU system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    obu = OBU(verbose=args.verbose)
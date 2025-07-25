# File: OBU.py
# This file is part of the VACOP project.
# Created by Rémi Myard
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License

# Execute : python3 -m back_part.OBU -v


from CAN_system.CANSystem_p import CANSystem
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
        self.running = True

        self.canSystem.set_callback(self.on_can_message)
        self._change_mode("INITIALIZE")
    
    def on_can_message(self, _, messageType, data):
        """Callback function"""
        match messageType:
            case "brake_rdy":
                self._handle_brake_ready()
            case "steer_rdy":
                self._handle_steer_ready()
            case "accel_pedal":
                self._handle_accel_pedal(data)
            case "brake_enable":
                self._handle_brake_enable()
            case "bouton_park":
                self._handle_bouton_park()
            case "bouton_auto_manu":
                self._handle_bouton_auto_manu(data)
            case "bouton_on_off":
                self._handle_bouton_on_off(data)
            case "bouton_reverse":
                self._handle_bouton_reverse()
            case "steer_pos_set":
                self._handle_steer_pos_set(data)
            case _:
                self._handle_event(messageType, data)
    
    # === Individual Message Handlers ===
    
    def _handle_brake_ready(self):
        if self.mode == "INITIALIZE":
            self.readyComponents.add("brake_rdy")
            self._check_ready()

    def _handle_steer_ready(self):
        if self.mode == "INITIALIZE":
            self.readyComponents.add("steer_rdy")
            self._check_ready()

    def _check_ready(self):
        if "brake_rdy" in self.readyComponents and "steer_rdy" in self.readyComponents:
            self._change_mode("START")

    def _handle_accel_pedal(self, data):
        if self.mode not in {"MANUAL", "AUTO"}:
            print(f"ERROR: Cannot set torque in mode '{self.mode}'")
            return
        try:
            torque_value = float(data) * TORQUE_SCALE
            self.motors.set_torque(torque_value)
            print("New torque = ", torque_value)
        except Exception:
            print(f"ERROR: Invalid torque data: {data}")

    def _handle_brake_enable(self):
        print("Shutdown requested via brake_enable.")
        self.shutdown()

    def _handle_bouton_on_off(self, data):
        # Temporary fallback to reverse handler since reverse button is not physically connected
        self._handle_bouton_reverse(data)

    def _handle_bouton_reverse(self, data):
        newState = "FORWARD" if data == 1 else "REVERSE"
        self._change_state(newState)

    def _handle_bouton_auto_manu(self, data):
        newMode = "MANUAL" if data == 1 else "AUTO"
        self._change_mode(newMode)

    def _handle_bouton_park(self):
        print("PARK button pressed: behavior not implemented.")

    def _handle_steer_pos_set(self, data):
        if self.mode not in {"AUTO"}:
            print(f"ERROR: Cannot set steer in mode '{self.mode}'")
            return
        self.canSystem.can_send("STEER", "steer_pos_set", data)

    def _handle_event(self, messageType, data):
        print(f"[Unhandled] {messageType}, data: {data}, state: {self.state}")

    # === Mode Management ===

    def _change_mode(self, newMode):
        self.mode = newMode
        match newMode:
            case "INITIALIZE":
                self._initialize_components()
            case "START":
                self._change_mode("AUTO")
            case "MANUAL":
                self._enter_manual_mode()
            case "AUTO":
                self._enter_auto_mode()
            case "ERROR":
                self._change_mode("INITIALIZE")
            case "OFF":
                self.shutdown()
            case _:
                print(f"Unknown mode '{newMode}'")
                self._change_mode("OFF")
    
    # = Mode Handlers =

    def _initialize_components(self):
        self.canSystem.can_send("BRAKE", "start", 0)
        time.sleep(0.2)
        self.canSystem.can_send("STEER", "start", 0)
        self.canSystem.start_listening()

    def _enter_manual_mode(self):
        print("MANUAL mode activated.")
        self._change_state("FORWARD")
        self.canSystem.can_send("STEER", "steer_enable", False)

    def _enter_auto_mode(self):
        print("AUTO mode activated.")
        self.canSystem.can_send("STEER", "steer_enable", True)
        #self.canSystem.can_send("STEER", "steer_pos_set", 700)
    

    # === State Management ===

    def _change_state(self, newState):
        self.state = newState
        match newState:
            case "FORWARD":
                self._enter_forward_state()
            case "REVERSE":
                self._enter_reverse_state()
            case "ERROR":
                self._change_mode("ERROR")

    # = State Handlers =

    def _enter_forward_state(self):
        self.motors.set_forward()

    def _enter_reverse_state(self):
        self.motors.set_reverse()

    # === Others ===

    def shutdown(self):
        if not self.running:
            return
        print("Shutting down system...")
        self.running = False
        try:
            self.canSystem.can_send("BRAKE", "stop", 0)
            self.canSystem.can_send("STEER", "stop", 0)
            self.canSystem.stop()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        print("System shutdown complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OBU system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    obu = OBU(verbose=args.verbose)

    try:
        while obu.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received.")
        obu.shutdown()
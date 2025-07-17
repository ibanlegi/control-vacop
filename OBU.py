from CAN_system.can_system import CANSystem
from DualMotorController import DualMotorController

MAX_TORQUE = 20.0
TORQUE_SCALE = MAX_TORQUE / 1023.0

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.motors = DualMotorController(verbose=self.verbose)
        self.can_system = CANSystem(verbose=self.verbose)
        self.can_system.set_callback(self.on_can_message)

        self.tabRdy_rcv = set()
        self.mode = None
        self.state = None

        self.change_mode("INITIALIZE")

    def change_mode(self, new_mode):
        self.mode = new_mode
        match self.mode:
            case "INITIALIZE":
                self.can_system.send("BRAKE", "start", 0)
                self.can_system.start_listening()
            case "START":
                self.change_mode("MANUAL")
            case "MANUAL":
                self.change_state("FORWARD")
            case "AUTO":
                print("AUTO mode not implemented.")
            case "ERROR":
                self.change_mode("INITIALIZE")
            case "OFF":
                self.on_ending()
            case _:
                print(f"Unknown mode '{self.mode}'")
                self.change_mode("OFF")

    def change_state(self, new_state):
        self.state = new_state
        match self.state:
            case "FORWARD":
                self.motors.set_forward()
            case "REVERSE":
                self.motors.set_reverse()
            case "ERROR":
                self.change_mode("ERROR")

    def on_can_message(self, _, message_type, data):
        match message_type:
            case "brake_rdy" | "steer_rdy":
                self.on_rdy(message_type)
            case "accel_pedal":
                self.on_set_torque(data)
            case "brake_enable":
                self.on_ending()
            case _:
                self.handle_event(message_type, data)

    def on_rdy(self, msg_type):
        if self.mode == "INITIALIZE" and msg_type not in self.tabRdy_rcv:
            self.tabRdy_rcv.add(msg_type)
            if len(self.tabRdy_rcv) > 0:
                self.change_mode("START")

    def on_set_torque(self, data):
        if self.mode not in {"MANUAL", "AUTO"}:
            print(f"ERROR: Cannot set torque in mode '{self.mode}'")
            return
        try:
            torque_value = float(data) * TORQUE_SCALE
            self.motors.set_torque(torque_value)
        except Exception:
            print(f"ERROR: Invalid torque data: {data}")

    def handle_event(self, message_type, data):
        print(f"[Unhandled] {message_type}, data: {data}, state: {self.state}")

    def on_ending(self):
        print("Shutting down...")
        self.can_system.stop()

if __name__ == "__main__":
    obu = OBU(verbose=True)
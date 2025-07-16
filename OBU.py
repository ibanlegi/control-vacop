from DualMotorController import DualMotorController
import can
from CAN_system.class_CanManager import CANManager, CANReceiver
from VehicleController import VehicleController

MAX_TORQUE = 20.0
TORQUE_SCALE = MAX_TORQUE / 1023.0
NO_BRAKE = 600 

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)
        self.motors = DualMotorController(verbose=self.verbose)
        self.can_manager = CANManager(self.bus)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])

        self.vehicleController = VehicleController()
        self.tabRdy_rcv = set()
        self.running = False
        self.mode = None
        self.state = None

        self.change_mode("INITIALIZE")
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def change_mode(self, new_mode):
        self.mode = new_mode
        self._print(f"Mode changed to: {self.mode}")

        match self.mode:
            case "INITIALIZE":
                self.can_manager.can_send("BRAKE", "start", 0)
                print("Entering INITIALIZE mode...")
                self.bus_listen()
            case "START":
                self.change_mode("MANUAL")  # Default mode after START
            case "MANUAL":
                self.change_state("FORWARD")
            case "AUTO":
                print("AUTO mode not yet implemented.")
            case "ERROR":
                self.change_mode("INITIALIZE")
            case "OFF":
                self.on_ending()
            case _:
                print(f"Unknown mode '{new_mode}'. Switching to OFF.")
                self.mode = "OFF"

    def change_state(self, new_state):
        self.state = new_state
        self._print(f"State changed to: {self.state}")

        match self.state:
            case "FORWARD":
                self.motors.set_forward()
            case "REVERSE":
                self.motors.set_reverse()
            case "ERROR":
                self.state = None
                self.change_mode("ERROR")
            case _:
                print(f"Unknown state: {new_state}")

    def on_rdy(self, message_type):
        if self.mode == "INITIALIZE" and message_type not in self.tabRdy_rcv:
            self.tabRdy_rcv.add(message_type)
            if len(self.tabRdy_rcv) > 0:  # Modifier si plusieurs "rdy" requis
                self.change_mode("START")

    def on_set_torque(self, data):
        if self.mode not in {"MANUAL", "AUTO"}:
            print(f"ERROR: Cannot set torque in mode '{self.mode}'")
            return

        try:
            torque_value = float(data) * TORQUE_SCALE
            self.motors.set_torque(torque_value)
        except (ValueError, TypeError):
            print(f"ERROR: Invalid torque data received: {data}")

    def msg_handling(self, message_type, data):
        match message_type:
            case "brake_rdy" | "steer_rdy":
                self._print(f"Received {message_type}")
                self.on_rdy(message_type)
            case "accel_pedal":
                self.on_set_torque(data)
            case "brake_enable":
                self.on_ending()
            case _:
                self.handle_event(message_type, data)

    def handle_event(self, message_type, data):
        print(f"[Unhandled] Message: {message_type}, Data: {data} in state {self.state}")

    def on_ending(self):
        print("Shutting down CAN bus and cleanup.")
        self.running = False
        self.bus.shutdown()

    def bus_listen(self):
        print("Starting CAN bus listening...")
        try:
            self.running = True
            previous_msg = None
            while self.running:
                current_msg = self.listener.can_input()
                if current_msg and current_msg != previous_msg:
                    previous_msg = current_msg
                    _, message_type, data = current_msg
                    print(f"Received → Type: {message_type}, Data: {data}")
                    self.msg_handling(message_type, data)
        except KeyboardInterrupt:
            print("Manual interrupt received.")
        finally:
            self.on_ending()

if __name__ == "__main__":
    obu = OBU(verbose=False)

import argparse
import time

RESET = '\033[0m'
BLUE = '\033[94m'


class MotorController:
    def __init__(self, node, stoPin, verbose=False):
        if not isinstance(node, int):
            raise TypeError(f"ERROR: node ({node}) is not type int")
        if not isinstance(stoPin, int):
            raise TypeError(f"ERROR: stoPin ({stoPin}) is not type int")
        self.node = node
        self.stoPin = stoPin
        self.verbose = verbose
        self._initialize_STO()
        self._initialize_motor()
        # Variables for simuling
        self._torqueTest = 0
        self._directionTest = "CW"
    
    def __del__(self):
        self.stop_motor()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[",self.node,"]",*args, **kwargs)

    def _initialize_STO(self):
        self._print("Init STO  with ",self.stoPin)
        print(BLUE + f"[Simulated GPIO] Initializing STO pin {self.stoPin} (set to HIGH)" + RESET)

    def _initialize_motor(self):
        self._print("Trying to Connect To SOLO")
        print(BLUE + f"[Simulated SOLO] Connecting to motor controller node {self.node}..." + RESET)
        time.sleep(1)
        self._print("Communication Established successfully!")

    def configure(self):
        print(BLUE + "[Simulated SOLO] Configuring motor..." + RESET)
        self._print("Identifying the Motor")
        time.sleep(5)
        self._print("End Configuration")

        print(BLUE + "[Simulated SOLO] Hall Sensor calibration..." + RESET)
        self._print("Hall Sensor calibration")
        time.sleep(10)
        self._print("End Calibration")

    def stop_motor(self):
        self._stop_torque()
        self._stop_STO()

    def _stop_STO(self):
        print(BLUE + "[Simulated GPIO]" + RESET)
        self._print("[STO] signal set to LOW: Safe Torque Off activated")

    def _stop_torque(self):
        print(BLUE + "[Simulated SOLO] Torque set to zero: motor stopped" + RESET)
        self._torqueTest = 0.
        self.display_torque()
        self._print("[Motor] torque set to zero: motor stopped")

    def display_torque(self):
        print(BLUE + f"[Simulated SOLO] Measured Iq/Torque [A]: {self._torqueTest} | Error: None" + RESET)

    def display_speed(self):
        print(BLUE + "[Simulated SOLO] Motor Speed [RPM]: 0 | Error: None" + RESET)

    def display_direction(self):
        print(BLUE + f"[Simulated SOLO] Set direction: {self._directionTest} | Error: None" + RESET)

    def set_direction(self, direction_str):
        direction_str = direction_str.upper()
        if direction_str not in ["CW", "CCW"]:
            raise ValueError(f"[{self.node}]ERROR: '{direction_str}' is not valid (CW, CCW)")
        print(BLUE + f"[Simulated SOLO] Motor direction set to {direction_str}" + RESET)
        self._directionTest = direction_str
        if self.verbose: self.display_direction()

    def set_torque(self, torque_value):
        try:
            torque_value = float(torque_value)
        except ValueError:
            raise ValueError(f"[{self.node}]ERROR: '{torque_value}' is not a valid float")
        if torque_value < 0:
            raise ValueError(f"[{self.node}]ERROR: torque must be non-negative")
        print(BLUE + f"[Simulated SOLO] Torque set to {torque_value} A" + RESET)
        self._torqueTest = torque_value
        if self.verbose: self.display_torque()

    def display_configuration(self):
        print(BLUE + "Initial Configuration of the Device and Motor \n" + RESET)
        print(BLUE + "PWM frequency: 20 kHz | Error: None" + RESET)
        print(BLUE + "Current limit: 10 A | Error: None" + RESET)
        print(BLUE + "Motor poles counts: 8 | Error: None" + RESET)
        print(BLUE + "Current controller KP: 0.5 | Error: None" + RESET)
        print(BLUE + "Current controller KI: 0.1 | Error: None" + RESET)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor control with direction and torque")
    parser.add_argument('node', type=int, help='Node identifier (required)')
    parser.add_argument('stoPin', type=int, help='Pin STO (required)')
    parser.add_argument('-d', '--direction', type=str, help='Motor direction (CW or CCW)')
    parser.add_argument('-t', '--torque', type=float, help='Torque value')
    parser.add_argument('-e', '--example', action='store_true', help='Run example mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    controller = MotorController(args.node, args.stoPin, args.verbose)

    try:
        if args.example:
            print("Execution example program")
            controller.set_direction("CW")
            controller.set_torque(10.)
            time.sleep(3)
            controller.set_direction("CCW")
            controller.set_torque(5.)
            time.sleep(3)

        elif args.direction or args.torque:
            if args.direction:
                print("Setting direction:", args.direction)
                controller.set_direction(args.direction)
            if args.torque is not None:
                controller.set_torque(args.torque)

        else:
            print("\nNo direction or torque provided, entering interactive mode.\n")
            while True:
                try:
                    action = input("Choose an action : \n\t[D] - Set direction \n\t[T] - Set torque\n> ").upper()
                    match action:
                        case 'D':
                            controller.display_direction()
                            direction = input("Enter direction [CW | CCW]: ").upper()
                            controller.set_direction(direction)
                        case 'T':
                            torque = input("Enter torque value (positive float): ")
                            controller.set_torque(torque)
                        case _:
                            print("Unknown action.")
                except Exception as e:
                    print(BLUE + f"Error: {e}")
                print()

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting...")
    finally:
        print("Ctrl+C : Quit")
        controller.stop_motor()

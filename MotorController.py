import SoloPy as solo
import RPi.GPIO as GPIO
import argparse
import time


class MotorController:
    def __init__(self, node, stoPin, verbose = False):
        if not isinstance(node, int):
            raise TypeError(f"[{self.node}]ERROR: node ({node}) is not type int")
        if not isinstance(stoPin, int):
            raise TypeError(f"[{self.node}]ERROR: stoPin ({stoPin}) is not type int")
        self.node = node
        self.stoPin = stoPin
        self.mySolo = None
        self.verbose = verbose
        self._initialize_STO()
        self._initialize_motor()
    
    def __del__(self):
        self.stop_motor()
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[",self.node,"]",*args, **kwargs)

    def _initialize_STO(self):
        self._print("Init STO  with ",self.stoPin)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.stoPin, GPIO.OUT)
        GPIO.output(self.stoPin, GPIO.HIGH)

    def _initialize_motor(self):
        self.mySolo = solo.SoloMotorControllersCanopen(self.node, solo.CanBusBaudRate.RATE_1000)
        self._print("Trying to Connect To SOLO")
        while True:
            time.sleep(1)
            connected, _ = self.mySolo.communication_is_working()
            if connected:
                break
        self._print("Communication Established successfully!")

    def configure(self):
        self.mySolo.set_command_mode(solo.CommandMode.DIGITAL)
        self.mySolo.set_motor_type(solo.MotorType.BLDC_PMSM)
        self.mySolo.set_feedback_control_mode(solo.FeedbackControlMode.HALL_SENSORS)
        self.mySolo.set_control_mode(solo.ControlMode.TORQUE_MODE)
        self.mySolo.motor_parameters_identification(solo.Action.START)
        self._print("Identifying the Motor")
        time.sleep(5)
        self._print("End Configuration")

        self.mySolo.sensor_calibration(solo.PositionSensorCalibrationAction.HALL_SENSOR_START_CALIBRATION)
        self._print("Hall Sensor calibration")
        time.sleep(10)
        self._print("End Calibration")

    def stop_motor(self):
        self._stop_torque()
        self._stop_STO()

    def _stop_STO(self):
        self._print("putting sto to low")
        GPIO.output(self.stoPin, GPIO.LOW)
        self._print("output LOW")
        self._print("[STO] signal set to LOW: Safe Torque Off activated")
    
    def _stop_torque(self):
        self.mySolo.set_torque_reference_iq(0.0)
        if self.verbose : self.display_torque()
        self._print("[Motor] torque set to zero: motor stopped")

    def display_torque(self):
        torque, error = self.mySolo.get_quadrature_current_iq_feedback()
        print(f"[{self.node}]Measured Iq/Torque [A]: {torque} | Error: {error}")

    def display_speed(self):
        speed, error = self.mySolo.get_speed_feedback()
        print(f"[{self.node}]Motor Speed [RPM]: {speed} | Error: {error}")

    def display_direction(self):
        direction, error = self.mySolo.get_motor_direction()
        print(f"[{self.node}]Set direction: {direction} | Error: {error}")

    def set_direction(self, direction_str):
        directions = {
            "CW" : solo.Direction.CLOCKWISE,
            "CCW": solo.Direction.COUNTERCLOCKWISE
        }
        direction_str = direction_str.upper()
        if direction_str not in directions:
            raise ValueError(f"[{self.node}]ERROR: '{direction_str}' is not valid (CW, CCW)")
        self.mySolo.set_motor_direction(directions[direction_str])
        if self.verbose : self.display_direction()

    def set_torque(self, torque_value):
        try:
            torque_value = float(torque_value)
        except ValueError:
            raise ValueError(f"[{self.node}]ERROR: '{torque_value}' is not a valid float")
        if torque_value < 0:
            raise ValueError(f"[{self.node}]ERROR: torque must be non-negative")

        self.mySolo.set_torque_reference_iq(torque_value)
        if self.verbose : self.display_torque()

    def display_configuration(self):
        print(f"[{self.node}]Initial Configuration of the Device and Motor \n")

        pwm_read, error = self.mySolo.get_output_pwm_frequency_khz()
        print(f"[{self.node}]PWM frequency: {pwm_read} kHz | Error: {error}")

        current_limit_read = self.mySolo.get_current_limit()
        print(f"[{self.node}]Current limit: {current_limit_read} A | Error: {error}")

        pole_count_read = self.mySolo.get_motor_poles_counts()
        print(f"[{self.node}]Motor poles counts: {pole_count_read} | Error: {error}")

        kp_read = self.mySolo.get_current_controller_kp()
        ki_read = self.mySolo.get_current_controller_ki()
        print(f"[{self.node}]Current controller KP: {kp_read} | Error: {error}")
        print(f"[{self.node}]Current controller KI: {ki_read} | Error: {error}")

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
                    print(f"Error: {e}")
                print()

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting...")
    finally:
        print("Ctrl+C : Quit")
        controller.stop_motor()

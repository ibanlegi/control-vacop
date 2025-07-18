import argparse
import time
from .MotorController_test import MotorController

class DualMotorController:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.m1 = MotorController(node=1, stoPin=16, verbose=self.verbose)
        self.m2 = MotorController(node=2, stoPin=26, verbose=self.verbose)

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
        
    def configure(self):
        self.m1.configure()
        self.m2.configure()

    def set_forward(self):
        self._print("Set forward")
        self.m1.set_direction("CW")
        self.m2.set_direction("CCW")

    def set_reverse(self):
        self._print("Set forward")
        self.m1.set_direction("CCW")
        self.m2.set_direction("CW")

    def set_torque(self, torque_value):
        self._print("Set torque : ", torque_value)
        self.m1.set_torque(torque_value)
        self.m2.set_torque(torque_value)

    def stop_motor(self):
        self._print("\t stop motors")
        self.m1.stop_motor()
        self.m2.stop_motor()
    
    def __del__(self):
        try:
            self._print("Destruct DualMotorController object")
            if hasattr(self, 'm1') and self.m1:
                self.m1.stop_motor()
            if hasattr(self, 'm2') and self.m2:
                self.m2.stop_motor()
        except Exception as e:
            print(f"Error in DualMotorController.__del__: {e}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DualMotorController system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    myMotorController = DualMotorController(verbose = args.verbose)


    myMotorController.configure()
    myMotorController.set_forward()

    myMotorController.set_torque(8)
    time.sleep(5)

    #myMotorController.set_torque(0)

    #time.sleep(10)

    #myMotorController.set_reverse()

    #myMotorController.set_torque(8)
    #time.sleep(5)

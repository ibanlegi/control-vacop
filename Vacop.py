import argparse
import time
from MotorController import MotorController

class Vacop:
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
        self.m1.stop_motor()
        self.m2.stop_motor()
    
    def __del__(self):
        self._print("Destruct vacop object")
        self.stop_motor()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vacop system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    myVacop = Vacop(verbose = args.verbose)

    myVacop.configure()
    time.sleep(5)
    myVacop.set_forward()

    myVacop.set_torque(8)
    time.sleep(5)

    myVacop.set_torque(0)

    time.sleep(1)

    myVacop.set_reverse()

    myVacop.set_torque(8)
    time.sleep(5)

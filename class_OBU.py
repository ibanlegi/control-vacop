from DualMotorController import DualMotorController
import can
import re
import time
from class_CanManager import CanManager

MAX_TORQUE = 20  # Maximum torque value for the motors

class OBU:
    def __init__(self, verbose=True):
        self.motors = DualMotorController(verbose=verbose)
        self.listener = CanManager()
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.prop_override = 0
        self.manual_prop_set = 0
        self.last_steer_enable = 0
        self.running = False


    def run(self):
        try:
            self.init()
            self.running = True
            while self.running:
                can_msg = self.listener.can_receive()
                if can_msg is not None: 
                    data = can_msg[2]
                    new_torque = int((data * MAX_TORQUE) / 1023)
                    if new_torque != self.motors.m1.get_torque():
                        self.motors.set_torque(new_torque)
                        print("New torque set:", new_torque)
        except KeyboardInterrupt:
            print("Arrêt manuel détecté.")
        finally:
            self.ending()

    def ending(self):
        print("Nettoyage...")
        self.motors.stop_motor()

if __name__ == "__main__":
    obu = OBU(verbose=True)
    obu.run()

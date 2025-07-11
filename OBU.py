""" File: OBU.py
# This file is part of the OBU project.
# Created by [Rémi Myard]
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License
"""

from DualMotorController import DualMotorController
import can
from CAN_system.class_CanManager import CANManager
from CAN_system.class_CanManager import CANReceiver

MAX_TORQUE = 20  # Maximum torque value for the motors

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose

        self.bus = can.interface.Bus(channel='vcan0', interface='socketcan', receive_own_messages=False)

        self.motors = DualMotorController(verbose = self.verbose)
        self.can_manager = CANManager(self.bus)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.prop_override = 0
        self.manual_prop_set = 0
        self.last_steer_enable = 0
        self.running = False


    def run(self):
        self.motors.set_forward()
        msg_prec = None
        try:
            self.can_manager.can_send("BRAKE", "start", 0)
            
            self.running = True
            while self.running:
                can_msg = self.listener.can_input()
                print(" CAN lecture")
                if can_msg is not None: 
                    if can_msg != msg_prec :
                        #print("can_msg = ", can_msg[2])
                        msg_prec = can_msg
                        if msg_prec != None :
                            value = (float(can_msg[2])*MAX_TORQUE/1023)
                            print("Value : ",value )
                            self.motors.set_torque(value)
                else:
                    print("No CAN message received ,stoping program")
                    self.running = False
        except KeyboardInterrupt:
            print("Arrêt manuel détecté.")
        finally:
            self.ending()

    def ending(self):
        print("\t \t Closing up and erasing...")
        self.bus.shutdown()
        # self.motors.stop_motor()

if __name__ == "__main__":
    obu = OBU(verbose=True)
    obu.run()

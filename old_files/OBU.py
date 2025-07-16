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
#from State_classes import *

MAX_TORQUE = 20  # Maximum torque value for the motors
MIN_TORQUE = MAX_TORQUE / 20

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose

        self.bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)

        self.motors = DualMotorController(verbose = self.verbose)
        self.canManager = CANManager(self.bus)
        self.listener = CANReceiver(self.canManager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.running = False
        #self.currentState = STARTED(I_State)


    def bus_listen(self):
        self.canManager.can_send("BRAKE", "start", 0)
        beforeMsg = None
        try:            
            self.running = True
            while self.running:
                currentMsg = self.listener.can_input()
                if currentMsg is not None: 
                    if currentMsg != beforeMsg :
                        beforeMsg = currentMsg
                        if beforeMsg != None :
                            data = currentMsg[2]
                            value = (float(data)*MAX_TORQUE/1023)
                            print("Value : ",value )
                            if value < MIN_TORQUE :
                                print("PEDALE LACHEE")
                            self.motors.set_torque(value)
        except KeyboardInterrupt:
            print("Arrêt manuel détecté.")
        finally:
            self.ending()

    def ending(self):
        print("\t \t Closing up and erasing...")
        self.bus.shutdown()

if __name__ == "__main__":
    obu = OBU(verbose=False)
    obu.bus_listen()

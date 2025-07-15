from DualMotorController import DualMotorController
import can
from CAN_system.class_CanManager import CANManager, CANReceiver

MAX_TORQUE = 20
MIN_TORQUE = MAX_TORQUE / 20
NO_BRAKE = 600

class State:
    def __init__(self, obu):
        self.obu = obu
        # self.valueBrake = 0
        self.valueAccelerate = 0
    def handle_message(self, message_type, data): pass

    # def on_init(self):
    #     pass

    # def on_shutoff(self):
    #     pass

    # def on_torque(self, value):
    #     pass
    def direction(self):
        pass

class OffState(State):
    def handle_message(self, message_type, data):
        if message_type == "stop":
            # TODO 
            print("TODO")
        elif message_type == "init":
            print("ajouter nouvel état dans Can_list pour l'envoi de 2e rpi à la fin de l'initialisation")
            self.obu.transition_to(StoppedState(self.obu))

class StoppedState(State):
    def handle_message(self, message_type, data):
        if message_type == "stop":
            self.obu.transition_to(OffState(self.obu))
        elif message_type == "accel_pedal":
            value = float(data) * MAX_TORQUE / 1023
            print("Accelerate Pedal Value:", value)
            if abs(value) > MIN_TORQUE:
                self.obu.motors.set_torque(value)
                self.obu.transition_to(AccelerateState(self.obu))
            self.old_valueAccelerate = value



class AccelerateState(State):
    def handle_message(self, message_type, data):
        if message_type == "accel_pedal":
            value = float(data) * MAX_TORQUE / 1023
            print("Accelerate Pedal Value:", value)
            if abs(value - self.old_valueAccelerate) > MIN_TORQUE:
                self.obu.motors.set_torque(value)
            else:
                print("PEDALE LACHEE")
                self.obu.motors.set_torque(0)
            self.old_valueAccelerate = value
        elif message_type == "brake_set" and data > NO_BRAKE: # verifier si c'est bien brake_set ou brake_pos ...
            self.obu.motors.set_torque(0) # modifier la valeur avec une fonction
            self.obu.transition_to(BrakeState(self.obu))

class BrakeState(State):
    def handle_message(self, message_type, data):
        if message_type == "accel_pedal":
            value = float(data) * MAX_TORQUE / 1023
            print("Accelerate Pedal Value:", value)
            if abs(value - self.old_valueAccelerate) > MIN_TORQUE:
                self.obu.transition_to(AccelerateState(self.obu))
                self.obu.motors.set_torque(value)
            else:
                print("PEDALE LACHEE")
                self.obu.motors.set_torque(0)
            self.old_valueAccelerate = value
        elif message_type == "brake_set" and data > NO_BRAKE: # verifier si c'est bien brake_set ou brake_pos ...
            self.obu.motors.set_torque(0) # modifier la valeur avec une fonction

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)
        self.motors = DualMotorController(verbose=self.verbose)
        self.can_manager = CANManager(self.bus)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.running = False
        self.state = OffState(self)

    # def transition_to(self, new_state):
    #     self.state = new_state

    def bus_listen(self):
        try:
            self.running = True
            self.state.on_init()
            beforeMsg = None
            while self.running:
                currentMsg = self.listener.can_input()
                if currentMsg is not None and currentMsg != beforeMsg:
                    beforeMsg = currentMsg
                    message_type = currentMsg[1]
                    data = currentMsg[2]
                    print(f"Message Type: {message_type}, Data: {data}")
                    self.state.handle_message(message_type, data)
                    if self.state == OffState(self): # and trouver condition d'arrêt
                        self.ending()
        except KeyboardInterrupt:
            print("Arrêt manuel détecté.")
            self.state.on_shutoff()
        finally:
            self.ending()

    def ending(self):
        print("\t\tClosing up and erasing...")
        self.bus.shutdown()

if __name__ == "__main__":
    obu = OBU(verbose=False)
    obu.bus_listen()

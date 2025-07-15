MAX_TORQUE = 20
MIN_TORQUE = MAX_TORQUE / 20
NO_BRAKE = 600


class State:
    def __init__(self, obu):
        self.obu = obu
        # self.valueBrake = 0
        self.valueAccelerate = 0

    def on_init(self, data): pass

    # def on_shutoff(self):
    #     pass

    # def on_torque(self, value):
    #     pass
    def direction(self):
        pass

class OffState(State):
    def on_init(self, data):
            print("ajouter nouvel état dans Can_list pour l'envoi de 2e rpi à la fin de l'initialisation")
            return StoppedState()

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

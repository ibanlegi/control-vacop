from DualMotorController import DualMotorController
import can
import time
from CAN_system.class_CanManager import CANManager, CANReceiver
from VehicleController import VehicleController

MAX_TORQUE = 20
MIN_TORQUE = MAX_TORQUE / 20
NO_BRAKE = 600

class OBU:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)
        self.motors = DualMotorController(verbose=self.verbose)
        self.can_manager = CANManager(self.bus)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.running = False
        self.vehicleController = VehicleController()
        self.mode = None
        self.state = None

        self.change_mode("INITIALIZE")
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[",self.node,"]",*args, **kwargs)
    
    def initialize_BRAKE(self):
        self._print("Trying to Connect To Brake device")
        while True:
            time.sleep(1)
            self.can_manager.can_send("BRAKE", "start", 0)
            currentMsg = self.listener.can_input()
            if currentMsg[1] == "brake_rdy":
                break
        self._print("Communication Established successfully with Brake device !")


    def change_mode(self, newMode):
        self.mode = newMode
        match self.mode:
            case "INITIALIZE":
                self.initialize_BRAKE()
                self.change_mode("START")
            case "START":
                self.bus_listen()
                self.change_mode("MANUAL") # Default
            case "MANUAL":
                self.change_state("FORWARD") # Default
            case "AUTO":
                print("A implémenter")
            case "ERROR":
                self.change_mode("INITIALIZE")
            case "OFF":
                self.on_ending()
            case _:
                print(f"{newMode} does not exist")
                self.mode = "OFF"
    
    def change_state(self, new_state):
        self.state = new_state
        match self.state:
            case "FORWARD":
                self.motors.set_forward()
            case "REVERSE":
                self.motors.set_reverse()
            case "ERROR":
                self.state = None
                self.change_mode("ERROR")

    def on_set_torque(self, data):
        if self.mode not in ["USER", "MANUAL"]:
            raise TypeError(f"ERROR: set torque ({data}) is not possible in {self.mode} mode")
        torqueValue = (float(data)*MAX_TORQUE/1023)
        if not isinstance(torqueValue, float):
            raise TypeError(f"ERROR: value ({torqueValue}) is not type float")
        self.motors.set_torque(torqueValue)

    def msg_handling(self, messageType, data):
        match messageType: 
            case "accel_pedal":
                self.on_set_torque(data)
            # TODO : Implémenter autres messages
            case _ :
                self.handle_event(self, messageType, data)

    def handle_event(self, messageType, data):
        print(f"Le type de message [{messageType}, {data}] n'est pas pris en charge dans l'état {self.state}")

    def on_ending(self):
        print("\t\tClosing up and erasing...")
        self.bus.shutdown()

    def bus_listen(self):
        try:
            self.running = True
            beforeMsg = None
            while self.running:
                currentMsg = self.listener.can_input()
                if currentMsg is not None and currentMsg != beforeMsg:
                    beforeMsg = currentMsg
                    messageType = currentMsg[1]
                    data = currentMsg[2]
                    print(f"Message Type: {messageType}, Data: {data}")
                    self.msg_handling(messageType, data)
                    
        except KeyboardInterrupt:
            print("Arrêt manuel détecté.")
            self.on_ending()
        finally:
            self.on_ending()

if __name__ == "__main__":
    obu = OBU(verbose=False)

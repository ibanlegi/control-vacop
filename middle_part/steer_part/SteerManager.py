import argparse
from AbstractClasses import AbstractController
import RPi.GPIO as GPIO
import time
import Adafruit_MCP3008
from CAN_system.CANSystem import CANSystem
import re

# Execute : python3 -m middle_part.steer_part.SteerManager -v

PWM_FREQ_STEER = 1000

# Set GPIO pins for stepper control
STEER_DIR_PIN= 17 # Direction GPIO Pin
STEER_PUL_PIN = 26 # Pulse GPIO Pin
STEER_EN_PIN = 16 # Enable GPIO Pin
BRAKE_PIN = 25 # Brake button GPIO Pin

# MCP3008 configuration
CLK = 21
MISO = 19
MOSI = 20
CS = 7

# Proportional gain (KP_STEER)
KP_STEER = 1

#Setup values of the steering actuator
STEER_LEFT_LIMIT = 100
STEER_RIGHT_LIMIT = 923
NEUTRAL_POSITION = 512

STEER_THRESHOLD = 10

class SteerManager(AbstractController):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.running = False
        self.steer_enable = False
        self.last_steer = NEUTRAL_POSITION
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([STEER_EN_PIN, STEER_PUL_PIN, STEER_DIR_PIN], GPIO.OUT)
        self.pulse = GPIO.PWM(STEER_PUL_PIN, PWM_FREQ_STEER)
        self.mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
        self.can_system = CANSystem(device_name="STEER",verbose=self.verbose)
        self.can_system.set_callback(self.treat_can_message)

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
    
    def read_steer_position(self):
        raw_position = self.mcp.read_adc(0)
        return raw_position
    
    def print_steer_position(self):
        position = self.read_steer_position()
        self._print(f"Steer position: {position}")

## -----------------Specific functions  ----------------- ##

    def put_steer_to_manual (self):
        self._print("Putting Steer to manual mode...")
        self.pulse.ChangeDutyCycle(0)
        self.pulse.stop()
        self.pulse.start(0)
        GPIO.output(STEER_EN_PIN, GPIO.HIGH)


    def apply_steer_control(self, position_wanted, force = False):
        if not self.steer_enable and not force: 
            self._print("Steering disabled ! ! nothing can be treated")
            self.put_steer_to_manual()
            return
            
        else :
            read_position = self.read_steer_position()
            error = position_wanted - read_position
            control_value = KP_STEER * error

            # Ensure control value is within limits to activate the motor
            if ( STEER_LEFT_LIMIT > read_position or read_position > STEER_RIGHT_LIMIT) :
                GPIO.output(STEER_EN_PIN, GPIO.HIGH)
                self._print("Steering out of bounds, disabling motor")
                return
            
            GPIO.output(STEER_EN_PIN, GPIO.LOW)
                
            # define the direction of the wheel spin 
            if control_value > STEER_THRESHOLD: 
                GPIO.output(STEER_DIR_PIN, GPIO.HIGH) #change direction
                self.pulse.ChangeDutyCycle(50) #send pulse

            elif control_value < -STEER_THRESHOLD:
                GPIO.output(STEER_DIR_PIN, GPIO.LOW) #change direction
                self.pulse.ChangeDutyCycle(50) #send pulse
            else :
                self.pulse.ChangeDutyCycle(0)
                self._print("Steering position is within threshold, no action taken")


    def move_to_target_position(self):
        """Move the steering actuator to the last set position."""
        actual_steer = self.read_steer_position()
        while abs(actual_steer - self.last_steer) > 5:
            self._print(f"Steer position we have: {actual_steer} || Steer position we want-> {self.last_steer}")
            self.apply_steer_control(self.last_steer)
            actual_steer = self.read_steer_position()
        self.pulse.ChangeDutyCycle(0)
        GPIO.output(STEER_EN_PIN, GPIO.HIGH)
        self._print("Reached target position\n")

    ## ----------------- Abstract Class functions ----------------- ##

    def wait_for_start(self) -> bool:
        """Waiting 'start' signal with the CAN"""
        self._print("waiting to start")
        while not self.running:
            can_msg = self.can_system.listener.can_input()
            if can_msg is not None:
                self._print("Received CAN message:", can_msg)
                if isinstance(can_msg, tuple) and len(can_msg) >= 3:
                    _, order_id, data = can_msg
                    self.treat_can_message(order_id, data)
        self._print("SteerManager received start signal.")
        return True
    
    def initialize(self):
        steer_position = self.read_steer_position()
        self._print(f"Steer position is {steer_position}, moving to neutral position...")
        while steer_position != NEUTRAL_POSITION:
            self._print(f"Steer position is {steer_position}, moving to neutral position...")
            self.apply_steer_control(NEUTRAL_POSITION, force = True)
            steer_position = self.read_steer_position()
            
        self.put_steer_to_manual()
        
        self.can_system.can_send("OBU", "steer_rdy", None)
        time.sleep(0.2)
        self.can_system.can_send("OBU", "steer_rdy", None)
        self.can_system.can_send("OBU", "steer_rdy", None)

        self._print("SteerManager initialized and ready.")

    def update(self):
        can_msg = self.can_system.listener.can_input()
        if can_msg and isinstance(can_msg, tuple) and len(can_msg) == 3 :
            self._print("Received CAN message:", can_msg)
            _, order_id, data = can_msg
            can_msg = None
            self.treat_can_message(order_id, data)
            
    def treat_can_message(self, order_id, data):
        self._print("my message type is ",order_id)
        if order_id == "start" : 
                self.running = True

        elif order_id =="stop" :           
                self.running = False
                return 
    
        elif order_id == "steer_enable":    
            self.steer_enable = data
            if not self.steer_enable :
                self._print("manual thing")
                self.put_steer_to_manual()
            else :
                GPIO.output(STEER_EN_PIN, GPIO.LOW)
            
        elif order_id == "steer_pos_set":  
                self.last_steer = data
                self.move_to_target_position()
        else :
                self._print(f"Unknown order_id: {order_id}")
                re.error(f"Unknown order_id: {order_id}")
                
    def stop(self):
        """Arrêt du système de direction."""
        self.pulse.ChangeDutyCycle(0)
        GPIO.output(STEER_EN_PIN, GPIO.HIGH)
        self._print("Steering disabled")
        GPIO.cleanup()
        self.pulse.stop()
        self.can_system.stop()
    
    def run(self):
        """Entrée principale du programme."""
        try:
            self.pulse.start(0)
            if self.wait_for_start():
                self.initialize()
                while self.running:
                    self.update()
        except KeyboardInterrupt:
            self._print("Interrupted by user.")
        finally:
            self.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeviceManager to steer vacop system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    manager = SteerManager(verbose=args.verbose)
    manager.run()

#new_steer.py
#17/07/2025
#Created by [Rémi Myard]
# Modified by Iban LEGINYIRA and Tinhinane AIT-MESSAOUD

#This code is hosted by the BRAKE DEVICE, it is controling the braking actuator and is receiving data from the accelerator pedal and manual braking button. 
#It can also control the steering for now but at the end of the project the steering will be controlled by a different node.

import RPi.GPIO as GPIO
import can
import time
import Adafruit_MCP3008
import re
import csv
from CAN_system.CANSystem import CANSystem


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

class SteerManager :
    def __init__ (self, verbose=False):
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([STEER_EN_PIN, STEER_PUL_PIN, STEER_DIR_PIN], GPIO.OUT)
        self.pulse = GPIO.PWM(STEER_PUL_PIN, PWM_FREQ_STEER)
        self.mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
        self.can_system = CANSystem(device_name="Steer",verbose=self.verbose)
        self.can_system.set_callback(self.treat_can_message)
    
        self.running = False
        self.last_steer = 0
        self.steer_enable = False
        
    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def read_steer_position(self):
        raw_position = self.mcp.read_adc(0)
        return raw_position
    
    def brake_override(self):
        self.can_system.send("OBU", "prop_override", int(GPIO.input(BRAKE_PIN) == GPIO.HIGH))

    def steer(self, position_wanted,enable):
        if not enable:
            self.pulse.ChangeDutyCycle(0)
            GPIO.output(STEER_EN_PIN, GPIO.HIGH)
            print("Steering disabled")
            return
    
        else :
            read_position = self.read_steer_position()
            error = position_wanted - read_position
            control_value = KP_STEER * error

            # Ensure control value is within limits to activate the motor
            if ( STEER_LEFT_LIMIT <= read_position and read_position <= STEER_RIGHT_LIMIT) :
                GPIO.output(STEER_EN_PIN, GPIO.LOW)
            else :
                GPIO.output(STEER_EN_PIN, GPIO.HIGH)
            
            # define the direction of the wheel spin 
            if control_value > STEER_THRESHOLD: 
                GPIO.output(STEER_DIR_PIN, GPIO.HIGH) #change direction
                self.pulse.ChangeDutyCycle(50) #send pulse

            elif control_value < -STEER_THRESHOLD:
                GPIO.output(STEER_DIR_PIN, GPIO.LOW) #change direction
                self.pulse.ChangeDutyCycle(50) #send pulse
            else:
                self.pulse.ChangeDutyCycle(0)

    def treat_can_message(self, message):
        order_id = message[1]
        data = message[2]
        match order_id : 
            case "start" :          
                self.running = True
            case "stop" :           
                self.running = False
                return 
            case "steer_enable":    self.steer_enable = data
            case "steer_pos_set":  self.last_steer = data
            case _ :
                self._print(f"Unknown order_id: {order_id}")
                re.error(f"Unknown order_id: {order_id}")
        
        actual_steer = self.read_steer_position()
        if actual_steer != self.last_steer:
            self._print(f"Steer position we have: { actual_steer} || Steer position we want-> {self.last_steer}")
            self.steer(self.last_steer, self.steer_enable)
        
    def initialize(self):
        while not self.running:
            self.can_system.start_listening()
            self._print("Waiting for start command...")
        self._print("SteerManager received true")

        steer_position = self.read_steer_position()
        while steer_position != NEUTRAL_POSITION:
            self._print(f"Steer position is {steer_position}, moving to neutral position...")
            self.steer(NEUTRAL_POSITION, True)
            steer_position = self.read_steer_position()
        
        self.can_system.send("OBU", "steer_rdy", None)
        self.can_system.send("OBU", "steer_rdy", None)
        self.can_system.send("OBU", "steer_rdy", None)

        self._print("SteerManager initialized and ready.")
    

    def main(self) : 
        try :
            self.pulse.start(0)  # Start PWM with 0% duty cycle
            GPIO.add_event_detect(BRAKE_PIN, GPIO.BOTH, callback=self.brake_override, bouncetime=20)
            while 1 :
                self.initialize()
                self._print("SteerManager is running...")
                while self.running:
                    self.can_system.start_listening()
                    time.sleep(0.1)
                    # the treatment of the can message is done in the callback function (treat_can_message)
                
                self.__print("SteerManager stopped.")
                self.steer(self.last_steer, False)


        except KeyboardInterrupt:
            self._print("SteerManager interrupted by user.")
            # self.extend_pwm.stop()
            # self.retract_pwm.stop()
            GPIO.cleanup()
        finally :
            self._print("Shutting Down SteerManager...")
            self.can_system.stop()
            self._print("SteerManager stopped.")
        
if __name__ == "__main__":
    manager = SteerManager(verbose=True)
    manager.main()
    

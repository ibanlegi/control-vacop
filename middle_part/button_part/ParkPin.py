# A tester 

import RPi.GPIO as GPIO
import time
from CAN_system.CANSystem import CANSystem


class ParkPin:
    def __init__(self, parkPin, verbose=False):
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        self.pin = parkPin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
        self.canSystem = CANSystem(device_name="STEER", verbose=True)
        self.previousState = GPIO.input(self.pin) # we consider that the button is not pressed when initialized
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._on_state_change, bouncetime=100)
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def _on_state_change(self, data):
        buttonState = GPIO.input(self.pin)
        if buttonState != self.previousState:
            self.previousState = buttonState
            self._print(f"Parking button {'pressed' if buttonState else 'released'}, button = {buttonState}")
            self.canSystem.can_send("OBU", "bouton_park", buttonState)
    
    def cleanup(self):
        GPIO.remove_event_detect(self.pin)

    def run(self):
        try:

            while True:
                time.sleep(1)  
        except KeyboardInterrupt:
            self._print("Interruption")
        finally:
            GPIO.cleanup()

if __name__ == "__main__":
    parkPin = ParkPin(22)
    parkPin.run()

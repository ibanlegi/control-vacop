# A tester 

import RPi.GPIO as GPIO
import time
from CAN_system.CANSystem import CANSystem


class ParkPin:
    def __init__(self, park_pin = 22):
        GPIO.setmode(GPIO.BCM)
        self.pin = park_pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
        self.can_system = CANSystem(device_name="STEER", verbose=True)
        self.previous_state = GPIO.input(self.pin) # we consider that the button is not pressed when initialized
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._on_state_change, bouncetime=100)
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def _on_state_change(self):
        button_state = GPIO.input(self.pin)
        if button_state != self.previous_state:
            self.previous_state = button_state
            self._print(f"Parking button {'pressed' if button_state else 'released'}, button = {button_state}")
            self.can_system.send("OBU", "bouton_park", button_state)
    
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
    park_pin = ParkPin()
    park_pin.run()
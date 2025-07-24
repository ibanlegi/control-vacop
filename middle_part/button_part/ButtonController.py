import RPi.GPIO as GPIO
from CAN_system.CANSystem import CANSystem
from AbstractClasses import AbstractController
import time

class ButtonController(AbstractController):
    def __init__(self, name, pin, verbose=False):
        self.pin = pin
        self.name = name
        self.verbose = verbose
        self.previousState = None
        self.canSystem = CANSystem(device_name="STEER", verbose=verbose)
        self.running = False

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def _on_state_change(self, channel):
        """Callback function for GPIO event"""
        buttonState = GPIO.input(self.pin)
        if buttonState != self.previousState:
            self.previousState = buttonState
            self._print(f"{self.name} button {'pressed' if buttonState else 'released'}, button = {buttonState}")
            self.canSystem.can_send("OBU", self.name, buttonState)
            time.sleep(0.05)

    def wait_for_start(self) -> bool:
        # Simple start condition, toujours prêt à démarrer
        return True

    def initialize(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.previousState = GPIO.input(self.pin) # we consider that the button is not pressed when initialized
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._on_state_change, bouncetime=100)
        self.running = True
        self._print(f"{self.name} initialized on pin {self.pin}")

    def stop(self):
        if self.running:
            GPIO.remove_event_detect(self.pin)
            GPIO.cleanup(self.pin)
            self.running = False
            self._print(f"{self.name} stopped and GPIO cleaned")

    def __del__(self):
        self._print(f"Destructor called for {self.name}, cleaning up GPIO...")
        self.stop()

    def update(self): pass

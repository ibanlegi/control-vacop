import argparse
import time
import RPi.GPIO as GPIO
from .ButtonController import ButtonController
from AbstractClasses import AbstractController

# Execute : python3 -m middle_part.button_part.DeviceManager -v

class DeviceManager:
    def __init__(self, controllers: list[AbstractController], verbose=False):
        self.verbose = verbose
        self.controllers = controllers
        self.running = True

    def run(self):
        self._print("Waiting for 'start' command from CAN...")
        try:
            while self.running:
                for controller in self.controllers:
                    if controller.wait_for_start():
                        self._print("Start received. Initializing...")
                        self.initialize_all()
                        self.main_loop()
                        return
                time.sleep(0.1)
        except KeyboardInterrupt:
            self._print("Interrupted by user. Exiting...")
            self.stop_all()

    def initialize_all(self):
        for controller in self.controllers:
            controller.initialize()

    def main_loop(self):
        self._print("Main loop started.")
        try:
            while self.running:
                for controller in self.controllers:
                    controller.update()
                time.sleep(0.05)
        except KeyboardInterrupt:
            self._print("Interrupted during main loop. Exiting...")
            self.stop_all()

    def stop_all(self):
        self.running = False
        self._print("Cleaning up controllers and GPIO...")
        for controller in self.controllers:
            controller.stop()
        GPIO.cleanup()
        self._print("Cleanup completed.")

    def __del__(self):
        self._print("Destructor called, cleaning up GPIO...")
        self.stop_all()
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[DeviceManager]", *args, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeviceManager to middle vacop system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    controllers = [
        ButtonController("bouton_park", 22, verbose=args.verbose),
        ButtonController("bouton_auto_manu", 23, verbose=args.verbose),
        ButtonController("bouton_on_off", 24, verbose=args.verbose),
        #ButtonController("bouton_reverse", None, verbose=args.verbose),
    ]

    manager = DeviceManager(controllers, verbose=args.verbose)
    manager.run()

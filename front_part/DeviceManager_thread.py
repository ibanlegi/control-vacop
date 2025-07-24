import argparse
import time
import threading
from .accelerator.sensor import AcceleratorSensor
from .accelerator.controller import AcceleratorController
from .CANAdapter import CANAdapter
from AbstractClasses import AbstractController

class DeviceManager:
    def __init__(self, controllers: list[AbstractController], verbose=False):
        self.verbose = verbose
        self.controllers = controllers
        self.running = True
        self.threads = []

    def run(self):
        self._print("Waiting for 'start' command from CAN in parallel...")
        try:
            for controller in self.controllers:
                thread = threading.Thread(target=self._controller_thread, args=(controller,))
                thread.start()
                self.threads.append(thread)

            while self.running:
                time.sleep(0.5)

        except KeyboardInterrupt:
            self._print("Interrupted by user. Exiting...")
            self.stop_all()

    def _controller_thread(self, controller: AbstractController):
        try:
            while self.running:
                try:
                    if controller.wait_for_start():
                        self._print(f"[{controller.name}] Start received. Initializing...")
                        controller.initialize()
                        break
                except Exception as e:
                    self._print(f"[{controller.name}] Error during wait_for_start(): {e}")
                time.sleep(0.1)

            while self.running:
                try:
                    controller.update()
                except Exception as e:
                    self._print(f"[{controller.name}] Error during update(): {e}")
                time.sleep(0.05)

        except Exception as e:
            self._print(f"[{controller.name}] Unexpected thread error: {e}")

    def stop_all(self):
        self.running = False
        for thread in self.threads:
            thread.join(timeout=1.0)
        for controller in self.controllers:
            try:
                controller.stop()
            except Exception as e:
                self._print(f"[{controller.name}] Error during stop(): {e}")
        self._print("All resources cleaned up.")

    def __del__(self):
        self._print("Destructor called, cleaning up...")
        self.stop_all()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[DeviceManager]", *args, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeviceManager to front vacop system")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    sensor = AcceleratorSensor(verbose=args.verbose)
    transport = CANAdapter(verbose=args.verbose)
    accel_controller = AcceleratorController(sensor, transport, verbose=args.verbose)

    manager = DeviceManager([accel_controller], verbose=args.verbose)
    manager.run()

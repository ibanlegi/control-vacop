import time
from .sensor import AcceleratorSensor
from AbstractClasses import AbstractController
from ..CANAdapter import CANAdapter

class AcceleratorController(AbstractController):
    def __init__(self, sensor: AcceleratorSensor, transport: CANAdapter, verbose=False):
        self.sensor = sensor
        self.transport = transport
        self.verbose = verbose
        self.running = False

    def wait_for_start(self):
        msg = self.transport.receive()
        if msg:
            _, order_id, _ = msg
            if order_id == "start":
                self.running = True
                return True
            elif order_id == "stop":
                self.running = False
        return False

    def initialize(self):
        for _ in range(3):
            self.transport.send("OBU", "brake_rdy")
            time.sleep(0.2)

    def update(self):
        if not self.running:
            return

        msg = self.transport.receive()
        if msg:
            _, order_id, _ = msg
            if order_id == "stop":
                self._print("Stop command received. Halting.")
                self.running = False
                return

        raw = self.sensor.read()
        clamped = self.sensor.clamp_acceleration(raw)
        mapped = self.sensor.map_to_output(clamped)

        if self.sensor.has_changed(mapped):
            self.transport.send("OBU", "accel_pedal", mapped)
    
    def stop(self):
        self.transport.stop()
    
    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[CTRL ACCELERATOR]", *args, **kwargs)

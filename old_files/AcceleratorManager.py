import time
import Adafruit_MCP3008
from CAN_system.CANSystem import CANSystem

ACCEL_THRESHOLD = 0

class AcceleratorManager:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.mcp = Adafruit_MCP3008.MCP3008(clk=21, cs=7, miso=19, mosi=20)
        self.can_system = CANSystem(verbose=self.verbose, device_name='BRAKE')
        self.lastAccelPedal = None
        self.running = True

    def __del__(self):
        self._print("Quitting AcceleratorManager...")

    def run(self):
        self.wait_for_start()
        self.initialize_system()
        self.main_loop()

    def wait_for_start(self):
        self._print("Waiting for start command from OBU...\n")
        while self.running:
            msg = self.receive_can_message()
            if msg:
                _, order_id, _ = msg
                if order_id == "start":
                    return
                elif order_id == "stop":
                    self._print("Received stop command during init. Exiting...")
                    self.running = False
                    return
            time.sleep(0.1)

    def initialize_system(self):
        self._print("Initializing system...\n")
        for _ in range(3):
            self.send_can_ready_signal()
            time.sleep(0.2)
        self._print("System initialized. Listening for further commands...\n")

    def main_loop(self):
        while self.running:
            self.check_for_stop_command()
            self.read_and_send_acceleration()
            time.sleep(0.05)

    def read_and_send_acceleration(self):
        raw_value = self.read_accelerator_raw()
        clamped = self.clamp_acceleration(raw_value)
        mapped = self.map_acceleration(clamped)

        if self.should_send(mapped):
            self.send_acceleration(mapped)

    def check_for_stop_command(self):
        msg = self.receive_can_message()
        if msg:
            _, order_id, _ = msg
            if order_id == "stop":
                self._print("Received stop command. Exiting...")
                self.running = False

    def read_accelerator_raw(self):
        value = int(self.mcp.read_adc(0))
        self._print(f"Raw accelerator value: {value}")
        return value

    def clamp_acceleration(self, value):
        return max(250, min(value, 875))

    def map_acceleration(self, value):
        mapped = int(((value - 250) / (875 - 250)) * 1023)
        self._print(f"Mapped accelerator value: {mapped}")
        return mapped

    def should_send(self, value):
        return self.lastAccelPedal is None or abs(value - self.lastAccelPedal) > ACCEL_THRESHOLD

    def send_acceleration(self, value):
        self.lastAccelPedal = value
        self.can_system.can_send("OBU", "accel_pedal", value)

    def send_can_ready_signal(self):
        self.can_system.can_send("OBU", "brake_rdy")

    def receive_can_message(self):
        return self.can_system.listener.can_input()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

if __name__ == "__main__":
    try:
        myAcceleratorManager = AcceleratorManager(verbose=True)
        myAcceleratorManager.run()
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")

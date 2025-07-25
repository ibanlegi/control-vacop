from CAN_system.CANSystem import CANSystem

class CANAdapter:
    def __init__(self, channel='can0', interface='socketcan', device_name='BRAKE', verbose=False):
        self.verbose = verbose
        self.canSystem = CANSystem(device_name=device_name, channel=channel, interface=interface, verbose=verbose)
        self.running = True

    def send(self, device_id, order_id, data=None):
        self._print(f"[CANAdapter] Sending {device_id=} {order_id=} {data=}")
        self.canSystem.can_send(device_id, order_id, data)

    def receive(self):
        # Returns the next CAN message as a tuple or None if no new message
        msg = self.canSystem.listener.can_input()
        if msg and isinstance(msg, tuple) and len(msg) == 3:
            self._print(f"[CANAdapter] Received message: {msg}")
            return msg
        return None

    def stop(self):
        self.running = False
        self.canSystem.stop()

    def _print(self, *args, **kwargs):
        if self.verbose:
            print("[CANAdapter]", *args, **kwargs)

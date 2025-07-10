import can

class CanReceive(can.Listener):
    def __init__(self, ui=None):
        super(CanReceive, self).__init__()
        self.last_received_message = None
        self.ui = ui  # Add a reference to the UserInterface instance
        self.last_data = {}  # Dictionary to store the last data for each device-order
        


    def on_message_received(self, msg):
        self.last_received_message = msg
    # Function to receive desired position from CAN bus
    def can_input(self):
        # Assuming self.last_received_message is the last received CAN message
        if self.last_received_message is None:
            return None  # Return None if no message has been received

        # Extract device_id and order_id from the arbitration ID
        device_value = hex(self.last_received_message.arbitration_id >> 8)[2:].zfill(2)
        order_value = hex(self.last_received_message.arbitration_id & 0xFF)[2:].zfill(2)

        # Extract data from the CAN message
        data = int.from_bytes(self.last_received_message.data, byteorder='big')

        # Convert hex values to human-readable strings
        device_id = device_id_reverse_map.get(device_value, device_value)
        order_id = order_id_reverse_map.get(order_value, order_value)

        if device_id == DEVICE:  # only process messages destined to this DEVICE
            key = (device_id, order_id)
            if key not in self.last_data or self.last_data[key] != data:
                message = f"received: {device_id} {order_id} {data}"
                # Log to the terminal
                if self.ui:
                    self.ui.log_to_terminal(message)
                # Update the last data
                self.last_data[key] = data
            # Return device_ID, order_id, and data in a tuple
            return device_id, order_id, data

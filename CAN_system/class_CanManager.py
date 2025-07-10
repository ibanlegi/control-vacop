import can
import re

DEVICE = "OBU"  # Define the DEVICE constant for this class

class CanManager:
    def __init__(self, can_list_file,ui=None):
        self.device_id_map, self.order_id_map, self.device_id_reverse_map, self.order_id_reverse_map = self.load_can_list("Can_List.txt")
        self.bus = can.interface.Bus(channel='can0', interface='socketcan')
        self.device_id_map = {}
        self.device_id_reverse_map = {}
        self.order_id_map = {}
        self.order_id_reverse_map = {}
        self.last_received_message = None
        self.ui = ui  # Add a reference to the UserInterface instance
        self.last_data = {} 

    def load_can_list(self,filename):
        with open(filename, 'r') as file:
            content = file.read()

        # Extract DeviceID mappings
        device_id_section = re.search(r'DeviceID:\s*{([^}]*)}', content)
        if device_id_section:
            device_lines = device_id_section.group(1).strip().split('\n')
            for line in device_lines:
                if '=' in line:
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    self.device_id_map[key] = value
                    self.device_id_reverse_map[value] = key

        # Extract OrderID mappings
        order_id_section = re.search(r'OrderID:\s*{([^}]*)}', content)
        if order_id_section:
            order_lines = order_id_section.group(1).strip().split('\n')
            for line in order_lines:
                if '=' in line:
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    self.order_id_map[key] = value
                    self.order_id_reverse_map[value] = key

        return self.device_id_map, self.order_id_map, self.device_id_reverse_map, self.order_id_reverse_map


    # Function to send message on the CAN bus
    def can_send(self,device_id, order_id, data=None, ui=None):
        
        # Convert human-readable IDs to their corresponding hex values
        device_value = self.device_id_map.get(device_id)
        order_value = self.order_id_map.get(order_id)

        if device_value is None or order_value is None:
            raise ValueError("Invalid device_id or order_id")

        # Create a CAN message with device_value followed by order_value
        arbitration_id = int(device_value + order_value, 16)

        # Convert the data into a list of bytes
        data_bytes = []
        if data is not None:
            while data > 0:
                data_bytes.insert(0, data & 0xFF)
                data >>= 8
            # Convert data back in decimal to display
            data = int.from_bytes(data_bytes, byteorder='big')

        # Create the CAN message
        can_message = can.Message(arbitration_id=arbitration_id, data=data_bytes, is_extended_id=False)
        
        # Convert data back in decimal to display
        data = int.from_bytes(data_bytes, byteorder='big')

        # Send the message on the CAN bus
        self.bus.send(can_message)
        message = f"sent: {device_id} {order_id} {data}"
        
        # Log to the terminal
        if ui:
            ui.log_to_terminal(message)
    # Function to receive desired position from CAN bus

    def can_receive(self):
        # Assuming self.last_received_message is the last received CAN message
        if self.last_received_message is None:
            return None  # Return None if no message has been received

        # Extract device_id and order_id from the arbitration ID
        device_value = hex(self.last_received_message.arbitration_id >> 8)[2:].zfill(2)
        order_value = hex(self.last_received_message.arbitration_id & 0xFF)[2:].zfill(2)

        # Extract data from the CAN message
        data = int.from_bytes(self.last_received_message.data, byteorder='big')

        # Convert hex values to human-readable strings
        device_id = self.device_id_reverse_map.get(device_value, device_value)
        order_id = self.order_id_reverse_map.get(order_value, order_value)

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

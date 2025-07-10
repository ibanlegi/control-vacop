# Fichier OBU de l'ancien projet :
# Il permet de réceptionner et traiter les instructions avec CAN

import can
import re
import time
from DualMotorController import DualMotorController

#Set the DEVICE as On Board Unit (OBU). It will be used to sort incoming can messages destined to this DEVICE
DEVICE = "OBU"

############################### FUNCTIONS ###########################################
MAX_TORQUE = 20  # Maximum torque value for the motors


# Function to load the CAN_List.txt 
# CAN_List.txt is a file containing DEVICE adresses and a list of orders. This file is basically an encryption DEVICE to read and write can messages. It can be easily modified and copy/pasted across all devices.
def load_can_list(filename):
    device_id_map = {}
    device_id_reverse_map = {}
    order_id_map = {}
    order_id_reverse_map = {}

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
                device_id_map[key] = value
                device_id_reverse_map[value] = key

    # Extract OrderID mappings
    order_id_section = re.search(r'OrderID:\s*{([^}]*)}', content)
    if order_id_section:
        order_lines = order_id_section.group(1).strip().split('\n')
        for line in order_lines:
            if '=' in line:
                key, value = line.split('=')
                key = key.strip()
                value = value.strip()
                order_id_map[key] = value
                order_id_reverse_map[value] = key

    return device_id_map, order_id_map, device_id_reverse_map, order_id_reverse_map


# Function to send message on the CAN bus
def can_send(device_id, order_id, data=None, ui=None):
    
    # Convert human-readable IDs to their corresponding hex values
    device_value = device_id_map.get(device_id)
    order_value = order_id_map.get(order_id)

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
    bus.send(can_message)
    message = f"sent: {device_id} {order_id} {data}"
    
    # Log to the terminal
    if ui:
        ui.log_to_terminal(message)

# Class to receive messages from the CAN bus
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



#################################### MAIN ###################################################

# Load CAN list mappings
device_id_map, order_id_map, device_id_reverse_map, order_id_reverse_map = load_can_list('./CAN_system/Can_List.txt')

bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)


def main():
    try:
        with can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False) as bus:
            motors = DualMotorController(verbose=True)
            # Start CAN bus
            message_listener = CanReceive()
            can.Notifier(bus, [message_listener])

            while True:
                # Initialize motors
                #init(message_listener)

                can_send("BRAKE", "start", 0)
                
                # Main operational loop
                running = True
                while running:
                    # Receive CAN message (from the devices: BRAKE or STEER)
                    can_msg = message_listener.can_input()
                    if can_msg != None :
                        print("can_msg = ", can_msg)
                        data = can_msg[2]
                        new_torque = int((data*MAX_TORQUE)/1023)
                        # I reckon the torque is the same in the two motors | we only test one value
                        if (new_torque != motors.m1.get_torque() ):
                            motors.set_torque(new_torque)
                            print("New torque set: ", new_torque)
            


    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        motors.stop_motor()
        del motors

if __name__ == "__main__":
    main()
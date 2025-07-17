import RPi.GPIO as GPIO
import can
import time
import Adafruit_MCP3008
import re
import csv

#Setup the bus
bus = can.interface.Bus(channel='can0', bustype='socketcan', receive_own_messages=False)

#Set the DEVICE as brake. It will setup the DEVICE id in the canbus
DEVICE = "BRAKE"


# MCP3008 configuration
CLK = 21
MISO = 19
MOSI = 20
CS = 7
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)


last_accel_pedal = None
ACCEL_THRESHOLD = 0

running = False


#######################################################################

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
    
device_id_map, order_id_map, device_id_reverse_map, order_id_reverse_map = load_can_list('../CAN_system/can_list.txt')

def can_send(device_ID, order_ID, data=None):
    # Convert human-readable IDs to their corresponding hex values
    device_value = device_id_map.get(device_ID)
    order_value = order_id_map.get(order_ID)

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
    #print("sent:", device_ID, order_ID, data)

class CanReceive(can.Listener):
    def __init__(self):
        super (CanReceive, self).__init__()
        self.last_received_message = None

    def on_message_received(self, msg):
        self.last_received_message = msg

    # Function to receive desired position from CAN bus
    def can_input(self):
        # Assuming self.last_received_message is the last received CAN message
        if self.last_received_message is None:
            return None  # Return None if no message has been received

        # Extract device_ID and order_ID from the arbitration ID
        device_value = hex(self.last_received_message.arbitration_id >> 8)[2:].zfill(2)
        order_value = hex(self.last_received_message.arbitration_id & 0xFF)[2:].zfill(2)

        # Extract data from the CAN message
        data = int.from_bytes(self.last_received_message.data, byteorder='big')

        # Convert hex values to human-readable strings
        device_ID = device_id_reverse_map.get(device_value, device_value)
        order_ID = order_id_reverse_map.get(order_value, order_value)

        if device_ID == DEVICE:
            
            #print("received:", device_ID, order_ID, data)
            # Return device_ID, order_ID, and data in a tuple
            return device_ID, order_ID, data


def read_accelerator():
    global last_accel_pedal
    
    # Read the current acceleration value from MCP3008
    accel_pedal = int(mcp.read_adc(0))
    print("acceleration :", accel_pedal)
    # Limit the value
    if accel_pedal < 250: #ancien = 170
        accel_pedal = 250
    elif accel_pedal > 875:
        accel_pedal = 875

    # Map the value
    accel_pedal = int(((accel_pedal - 250) / (875 - 250)) * 1023)

    # Check if the new value differs from the last value by more than the threshold
    if last_accel_pedal is None or abs(accel_pedal - last_accel_pedal) > ACCEL_THRESHOLD:
        # Update the last value
        last_accel_pedal = accel_pedal
        can_send("OBU","accel_pedal",accel_pedal)
    
def init(message_listener):
    global running
    print("waiting for starting order...\n")
    #We wait for the OBU to send the start message
    while running is False:
        can_msg = message_listener.can_input()
        if can_msg is not None:
            print("I received a messsage")
            # Extract data from the can message
            order_id = can_msg[1] #order_id is the order we received
            data = can_msg[2] #data is the data attached to the order
            if order_id == "start":
                running = True
    #Once the start message is received we start to initialise the actuators
    print("initialization...\n")
    can_send("OBU","brake_rdy")
    can_send("OBU","brake_rdy")
    can_send("OBU","brake_rdy")
    
    print("system initialized")
 


def main():
    global running
    global start_time
    try:
        with can.interface.Bus(channel='can0', bustype='socketcan', receive_own_messages=False) as bus:
            # Start CAN bus
            message_listener = CanReceive()
            can.Notifier(bus, [message_listener])

            while True:
                #Initialise de position of the actuator
                init(message_listener)
                print("System running.\n\n\n")
                start_time = time.time()#get time for the sensor_log file
                running = True
                while running:
                    # Receive CAN message
                    can_msg = message_listener.can_input()
                    print("can_msg = ",can_msg)
                    
                    # Read the value from the accelerator pedal and send the acceleration value on the can bus
                    read_accelerator()
                    print("lecture accelerateur")
                
                # When the actuator has been stopped by the OBU
                print("System stopped.\n\n\n")
                
                    

    
    except KeyboardInterrupt:
        print("KeyboardInterrupt")

    finally:
        # Close the CAN bus
        bus.shutdown()


if __name__ == "__main__":
    main()
     
	

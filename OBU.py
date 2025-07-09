#OBU.py
#18/07/24
#Rémi Myard

#This is the code of the On Board Unit of the VACOP
#It takes inputs from the user and the can_bus, takes decisions and commands all actuators (propulsion, braking, steering)



##################################### Setup ###################################



import RPi.GPIO as GPIO
import can
import re
import time

#Set the DEVICE as On Board Unit (OBU). It will be used to sort incoming can messages destined to this DEVICE
DEVICE = "OBU"

# Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Set PWM frequency (Hz)
PWM_FREQ_PROP = 5000

# Set GPIO pins for the propulsion controller
DIR_1_PIN = 23 #chose the direction of the motor1 (HIGH = CCW) (LOW = CW)
DIR_2_PIN = 17 #chose the direction of the motor2 (HIGH = CCW) (LOW = CW)
SET_TORQUE_1_PIN = 24 #set the current applied to motor 1
SET_TORQUE_2_PIN = 22 #set the current applied to motor 2
STO1_PIN = 16 #Set Torque Off motor 1
STO2_PIN = 26 #Set Torque Off motor 2

GPIO.setup(DIR_1_PIN, GPIO.OUT)
GPIO.setup(DIR_2_PIN, GPIO.OUT)
GPIO.setup(SET_TORQUE_1_PIN, GPIO.OUT)
GPIO.setup(SET_TORQUE_2_PIN, GPIO.OUT)
GPIO.setup(STO1_PIN, GPIO.OUT)
GPIO.setup(STO2_PIN, GPIO.OUT)

GPIO.output(DIR_1_PIN, GPIO.HIGH) #for now we can only go forward
GPIO.output(DIR_2_PIN, GPIO.LOW) #for now we can only go forward

# Initialize PWM pins
SetTorque1 = GPIO.PWM(SET_TORQUE_1_PIN, PWM_FREQ_PROP)
SetTorque2 = GPIO.PWM(SET_TORQUE_2_PIN, PWM_FREQ_PROP)

# Start PWM instances
SetTorque1.start(0)
SetTorque2.start(0)

# MCP3008 configuration
CLK = 21
MISO = 19
MOSI = 20
CS = 7
#mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

#Setup the can bus




############################### FUNCTIONS ###########################################



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


# Function to control the motors
# The motors are at the back of the car, with the OBU. The OBU controlls the motors with GPIO, no need for the can bus.
def propulsion(prop_set):
    # Map the value
    prop_set = int((prop_set * 100) / 1023)
    # Set the duty cycle of the motors
    SetTorque1.ChangeDutyCycle(prop_set)
    SetTorque2.ChangeDutyCycle(prop_set)

def propulsion_enable(enable):
    if enable is True :
        GPIO.output(STO1_PIN, GPIO.HIGH)
        GPIO.output(STO2_PIN, GPIO.HIGH)
    else:
        GPIO.output(STO1_PIN, GPIO.LOW)
        GPIO.output(STO2_PIN, GPIO.LOW)


def processor(can_msg, user_msg, ui=None):
    global prop_override
    global manual_prop_set
    global last_steer_enable
    # Extract data from the user message 
    on_off_state = user_msg[0] #0=off, 1=on
    driving_mode = user_msg[1] #0=manual, 1=auto
    auto_brake_set = user_msg[2] #0=NO_BRAKE, 1=FULL_BRAKE
    auto_steer_set = user_msg[3] #0=FullLeft, 512=middle,1023=FullRight
    auto_prop_set = user_msg[4] #0=No prop #1023 = FULL prop

    # Extract data from the can message
    if can_msg is not None :
        order_id = can_msg[1] #order_id is the order we received
        data = can_msg[2] #data is the data attached to the order

    #Manage order_id
    if can_msg is not None:
        if order_id == "prop_override" and data == 1:
            prop_override = 1 #modify the global variable prop_override if we detect that the user is braking
            
        if order_id == "prop_override" and data == 0:
            prop_override = 0

        if order_id == "accel_pedal":
            manual_prop_set = data
        

    #Manual mode
    if driving_mode == 0:
        #reset braking
        if ui.last_braking_mode is None or ui.last_braking_mode != 0:
            can_send("BRAKE", "brake_set", 0, ui)
            ui.last_braking_mode = 0

        #steering
        if last_steer_enable is None or last_steer_enable != 0:
            can_send("BRAKE", "steer_enable", 0, ui)
            last_steer_enable = 0
        
        #propulsion
        if prop_override == 0:
            propulsion(manual_prop_set)

        else:
            propulsion(0)

    #Automatic mode
    else:
        
        #Brake
        if ui.last_braking_mode is None or ui.last_braking_mode != auto_brake_set:
            if auto_brake_set == 1: #brake_set =1 means we want to brake
                can_send("BRAKE", "brake_set", 1, ui)
            else:  #auto_brake_ser == 0 means we are not braking
                can_send("BRAKE", "brake_set", 0, ui)
            ui.last_braking_mode = auto_brake_set
        
        #Propulsion
        if auto_brake_set == 0:
            propulsion(auto_prop_set)
        
        else:
            propulsion(0)

        
        #Steering
        if last_steer_enable is None or last_steer_enable != 1:
            can_send("BRAKE", "steer_enable", 1, ui)
            last_steer_enable = 1

        if ui.last_steering_value is None or ui.last_steering_value != auto_steer_set:
            #map value: 
            mapped_steering_value = int(((auto_steer_set+100)*1023)/200)
            can_send("STEER", "steer_pos_set", mapped_steering_value, ui)
            ui.last_steering_value = auto_steer_set


def init(message_listener):
    print("waiting for start...\n")

    # We enable movement of the actuators
    propulsion(0)
    propulsion_enable(True)#activate propulsion
    can_send("BRAKE","brake_enable",None)
    can_send("STEER","steer_enable",None)
    print("Ready to use")
    return




#################################### MAIN ###################################################

# Function to process can messages and user inputs
# Initialize variables
prop_override = 0
manual_prop_set = 0
last_steer_enable = 0


# Load CAN list mappings
device_id_map, order_id_map, device_id_reverse_map, order_id_reverse_map = load_can_list('CAN_List.txt')

bus = can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False)


def main():
    try:
        with can.interface.Bus(channel='can0', interface='socketcan', receive_own_messages=False) as bus:

            # Start CAN bus
            message_listener = CanReceive()
            can.Notifier(bus, [message_listener])

            while True:
                # Initialize VACOP
                #init(message_listener)

                can_send("BRAKE", "start", 0)
                
                # Main operational loop
                running = True
                while running:
                    # Receive CAN message (from the devices: BRAKE or STEER)
                    can_msg = message_listener.can_input()
                    if can_msg != None :
                        print("can_msg = ", can_msg)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        bus.shutdown()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
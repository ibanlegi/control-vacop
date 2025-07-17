""" File: class_CanManager.py
# This file is part of the OBU project.
# Created by [Rémi Myard]
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License
"""


import can
import re

class CANManager:
    def __init__(self,bus, device_name = 'OBU', can_list_path = 'CAN_system/can_list.txt', ui=None):
        self.device_name = device_name
        self.ui = ui
        self.device_id_map, self.order_id_map, self.device_id_reverse_map, self.order_id_reverse_map = self.load_can_list(can_list_path)
        self.bus = bus

    def load_can_list(self, filename):
        device_id_map, order_id_map = {}, {}
        device_id_reverse_map, order_id_reverse_map = {}, {}

        with open(filename, 'r') as file:
            content = file.read()

        for section_name, target_map, reverse_map in [
            ("DeviceID", device_id_map, device_id_reverse_map),
            ("OrderID", order_id_map, order_id_reverse_map)
        ]:
            section = re.search(fr'{section_name}:\s*{{([^}}]*)}}', content)
            if section:
                lines = section.group(1).strip().split('\n')
                for line in lines:
                    if '=' in line:
                        key, value = map(str.strip, line.split('='))
                        target_map[key] = value
                        reverse_map[value] = key

        return device_id_map, order_id_map, device_id_reverse_map, order_id_reverse_map

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

        


class CANReceiver(can.Listener):
    def __init__(self, manager: CANManager):
        super().__init__()
        self.manager = manager
        self.last_received_message = None
        self.last_data = {}

    def on_message_received(self, msg):
        self.last_received_message = msg

    def can_input(self):
        if self.last_received_message is None:
            return None

        arbitration_id = self.last_received_message.arbitration_id
        device_hex = hex(arbitration_id >> 8)[2:].zfill(2)
        order_hex = hex(arbitration_id & 0xFF)[2:].zfill(2)
        data = int.from_bytes(self.last_received_message.data, byteorder='big')

        device = self.manager.device_id_reverse_map.get(device_hex, device_hex)
        order = self.manager.order_id_reverse_map.get(order_hex, order_hex)

        if device == self.manager.device_name:
            key = (device, order)
            if key not in self.last_data or self.last_data[key] != data:
                if self.manager.ui:
                    self.manager.ui.log_to_terminal(f"received: {device} {order} {data}")
                self.last_data[key] = data
            return device, order, data

class CANSystem:
    def __init__(self, channel='can0', interface='socketcan', verbose=False):
        self.verbose = verbose
        self.bus = can.interface.Bus(channel=channel, interface=interface, receive_own_messages=False)
        self.can_manager = CANManager(self.bus)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.running = False
        self.callback = None  # callback to process messages

    def set_callback(self, callback_fn):
        #Sets the function to call when a message is received.
        self.callback = callback_fn

    def start_listening(self):
        # Starts listening to the CAN bus and dispatching messages to the callback.
        if self.verbose: print("CANSystem: Listening on CAN bus...")
        self.running = True
        previous_msg = None

        while self.running:
            msg = self.listener.can_input()
            if msg and msg != previous_msg:
                previous_msg = msg
                if self.callback:
                    self.callback(*msg)

    def stop(self):
        #Stops listening and shuts down the CAN bus.
        self.running = False
        self.bus.shutdown()

    def send(self, id_, sub_id, data):
        #Wrapper around CANManager send.
        self.can_manager.can_send(id_, sub_id, data)

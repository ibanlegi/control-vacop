# File: CANSystem.py
# This file is part of the OBU project.
# Created by Rémi Myard
# Modified by Iban LEGINYORA and Tinhinane AIT-MESSAOUD
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License

#----------------------------------------------------------------------------
# This system uses a FIFO (First In, First Out) queue to handle CAN messages.
# Messages are processed in the order in which they are received.
#----------------------------------------------------------------------------

import can
import re
import threading
import queue


class CANManager:
    def __init__(self, bus, device_name, can_list_path='CAN_system/can_list.txt'):
        self.device_name = device_name
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

    def can_send(self, device_id, order_id, data=None):
        device_value = self.device_id_map.get(device_id)
        order_value = self.order_id_map.get(order_id)

        if device_value is None or order_value is None:
            raise ValueError("Invalid device_id or order_id")

        arbitration_id = int(device_value + order_value, 16)

        data_bytes = []
        if data is not None:
            while data > 0:
                data_bytes.insert(0, data & 0xFF)
                data >>= 8

        can_message = can.Message(arbitration_id=arbitration_id, data=data_bytes, is_extended_id=False)
        self.bus.send(can_message)



class CANReceiver(can.Listener):
    def __init__(self, manager: CANManager):
        super().__init__()
        self.manager = manager
        self.last_data = {}
        self.msg_queue = queue.Queue()

    def on_message_received(self, msg):
        self.msg_queue.put(msg)

    def can_input(self):
        try:
            msg = self.msg_queue.get_nowait()
        except queue.Empty:
            return None

        arbitration_id = msg.arbitration_id
        device_hex = hex(arbitration_id >> 8)[2:].zfill(2)
        order_hex = hex(arbitration_id & 0xFF)[2:].zfill(2)
        data = int.from_bytes(msg.data, byteorder='big')

        device = self.manager.device_id_reverse_map.get(device_hex, device_hex)
        order = self.manager.order_id_reverse_map.get(order_hex, order_hex)
        if device == self.manager.device_name:
            return device, order, data
        return None



class CANSystem:
    def __init__(self,device_name, channel='can0', interface='socketcan', verbose=False):
        self.device_name = device_name
        self.verbose = verbose
        self.bus = can.interface.Bus(channel=channel, interface=interface, receive_own_messages=False)
        self.can_manager = CANManager(bus=self.bus, device_name=self.device_name)
        self.listener = CANReceiver(self.can_manager)
        self.notifier = can.Notifier(self.bus, [self.listener])
        self.running = False
        self.callback = None

    def set_callback(self, callback_fn):
        self.callback = callback_fn
    
    def start_listening(self):
        print("start_listen")
        if self.verbose:
            print("CANSystem: Listening on CAN bus...")

        self.running = True

        def listen_loop():
            previous_msg = None
            while self.running:
                msg = self.listener.can_input()
                if msg and isinstance(msg, tuple) and len(msg) == 3 and msg != previous_msg:
                    previous_msg = msg
                    if self.callback:
                        self.callback(*msg)

        self.listen_thread = threading.Thread(target=listen_loop)
        self.listen_thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, "listen_thread"):
            self.listen_thread.join()
        self.bus.shutdown()


    def can_send(self, id_, sub_id, data=None):
        self.can_manager.can_send(id_, sub_id, data)

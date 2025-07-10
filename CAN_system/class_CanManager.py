import can
import re

DEVICE = "OBU"  # Define the DEVICE constant for this class

class CanManager:
    def __init__(self):
        self.device_id_map = {}
        self.device_id_reverse_map = {}
        self.order_id_map = {}
        self.order_id_reverse_map = {}
        self.last_data = {}
        self.last_received_message = None
        self.ui = None  # Ajout si jamais utilisé
        self.load_can_list("./CAN_system/Can_List.txt")

        try:
            self.bus = can.interface.Bus(channel='can0', interface='socketcan')
        except can.CanError as e:
            print(f"Erreur d'initialisation du bus CAN : {e}")
            self.bus = None

    def load_can_list(self, filename):
        def parse_section(section_name, target_map, reverse_map):
            pattern = rf'{section_name}:\s*{{(.*?)}}'
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                print(f"[WARN] Section {section_name} non trouvée.")
                return
            lines = match.group(1).strip().split('\n')
            for line in lines:
                if '=' in line:
                    key, value = map(str.strip, line.split('=', 1))
                    if key and value:
                        target_map[key] = value
                        reverse_map[value] = key
                    else:
                        print(f"[WARN] Ligne malformée dans {section_name}: '{line}'")
                elif line.strip():  # ligne non vide
                    print(f"[WARN] Ligne invalide dans {section_name}: '{line}'")

        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"[ERREUR] Fichier non trouvé: {filename}")
            return

        parse_section('DeviceID', self.device_id_map, self.device_id_reverse_map)
        parse_section('OrderID', self.order_id_map, self.order_id_reverse_map)

    def can_send(self, device_id, order_id, data=None, ui=None):
        device_value = self.device_id_map.get(device_id)
        order_value = self.order_id_map.get(order_id)

        if device_value is None or order_value is None:
            raise ValueError(f"ID invalide: device_id={device_id}, order_id={order_id}")

        arbitration_id = int(device_value + order_value, 16)

        # Convert data to bytes
        data_bytes = []
        if data is not None:
            if not isinstance(data, int):
                raise TypeError("`data` doit être un entier")
            data_bytes = data.to_bytes((data.bit_length() + 7) // 8 or 1, 'big')

        if self.bus:
            try:
                can_message = can.Message(arbitration_id=arbitration_id, data=data_bytes, is_extended_id=False)
                self.bus.send(can_message)
                message = f"sent: {device_id} {order_id} {int.from_bytes(data_bytes, 'big')}"
                if ui:
                    ui.log_to_terminal(message)
            except can.CanError as e:
                print(f"[ERREUR] Échec d'envoi CAN: {e}")
        else:
            print("[ERREUR] Bus CAN non initialisé.")

    def can_receive(self):
        if self.last_received_message is None:
            return None

        arbitration_id = self.last_received_message.arbitration_id
        device_value = f"{(arbitration_id >> 8) & 0xFF:02X}"
        order_value = f"{arbitration_id & 0xFF:02X}"

        data = int.from_bytes(self.last_received_message.data, byteorder='big')

        device_id = self.device_id_reverse_map.get(device_value, device_value)
        order_id = self.order_id_reverse_map.get(order_value, order_value)

        if device_id == DEVICE:
            key = (device_id, order_id)
            if self.last_data.get(key) != data:
                message = f"received: {device_id} {order_id} {data}"
                if self.ui:
                    self.ui.log_to_terminal(message)
                self.last_data[key] = data

            return device_id, order_id, data
        return None

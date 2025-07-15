import gc
from State_classes import *

class VehicleController:
    def __init__(self):
        self.state = OffState(self)
    
    def on_init(self, data):
        self.change_state(self.state.on_init(data))

    def change_state(self, new_state_class):
        #if hasattr(self.state, "__del__"):
        #    self.state.__del__()
        del self.state
        gc.collect()
        self.state = new_state_class(self)

    def handle_event(self, event_name, *args):
        method = getattr(self.state, event_name, None)
        if method:
            method(*args)
        else:
            print(f"L'événement '{event_name}' n'est pas disponible dans {self.state.__class__.__name__}")

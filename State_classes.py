from OBU import OBU

class I_State:
    OBU = OBU()

    def initialize_system(self): pass
    def stop_pressed(self): pass
    def clean_exit(self): pass    
    def direction_button_pressed(self): pass   
    def direction_changed_event(self): pass
    def accelerator_pressed(self): pass
    def accelerator_released(self): pass
    def brake_pressed(self): pass
    def brake_released(self): pass


class STARTED(I_State):
    def initialize_system(self):
        print("System initialized")
        return STOPPED()

class STOPPED(I_State):
    def direction_button_pressed(self):
        return REVERSING()
    
    def accelerator_pressed(self):
        return ACCELERATING()
    
    def brake_pressed(self):
        return BRAKING()
    
    def stop_pressed(self):
        return OFF()

class ACCELERATING(I_State):
    def accelerator_released(self):
        return ACTIVE()

    def brake_pressed(self):
        return BRAKING()

class BRAKING(I_State):
    def brake_released(self):
        return  ACTIVE()

class ACTIVE(I_State):
    #def __init__ (self):
        #if self.OBU.motors == 0:
        #    return STOPPED
        
    def accelerator_pressed(self):
        return ACCELERATING()

    def brake_pressed(self):
        return BRAKING()

class REVERSING(I_State):
    def direction_changed_event(self):
        return STOPPED()

class OFF(I_State):
    def clean_exit(self):
        print("System shut down")

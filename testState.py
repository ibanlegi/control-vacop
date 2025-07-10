from State_classes import *


if __name__ == "__main__":
    state = {
        1 : "initialize_system",
        2 : "stop_pressed",
        3 : "clean_exit",
        4 : "direction_button_pressed",
        5 : "direction_changed_event",
        6 : "accelerator_pressed",
        7 : "accelerator_released",
        8 : "brake_pressed",
        9 : "brake_released",
        10 : "exit"
    }

    current_state = STARTED()
    print(f"Initial State : {current_state.__class__.__name__}")

    while True:
        print("\nÉvénements disponibles :")
        print("1  - initialize_system")
        print("2  - stop_pressed")
        print("3  - clean_exit")
        print("4  - direction_button_pressed")
        print("5  - direction_changed_event")
        print("6  - accelerator_pressed")
        print("7  - accelerator_released")
        print("8  - brake_pressed")
        print("9  - brake_released")
        print("10 - exit (quitter le simulateur)\n")
        event = int(input("Enter an event : "))

        if state[event] == "exit":
            print("Simulation down.")
            break

        if not hasattr(current_state, state[event]):
            print("Invalid event.")
            continue

        method = getattr(current_state, state[event])
        result = method()

        if isinstance(result, I_State):
            print(f"Transition to : {result.__class__.__name__}")
            current_state = result
        else:
            print(f"No changing state ({current_state.__class__.__name__})")

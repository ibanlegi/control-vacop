import argparse
import time
from CAN_system.CANSystem import CANSystem
import queue
import threading
import curses


def main(stdscr):
    # Initialisation curses
    curses.curs_set(0)  # Cache le curseur
    stdscr.nodelay(True)  # Pas de blocage sur input
    stdscr.timeout(100)   # Timeout pour la boucle de lecture

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    args, _ = parser.parse_known_args()

    can = CANSystem(verbose=args.verbose, device_name="KEYBOARD_DRIVER")
    can.start_listening()
    #can = FakeCANBus()
    #can.start()

    accel = 0
    steer = 512  # Position neutre

    stdscr.addstr(0, 0, "[CAN Keyboard Driver Started]", curses.A_BOLD)

    try:
        while True:
            stdscr.addstr(2, 0, "=== CONTROL MENU ===")
            stdscr.addstr(3, 0, "w: Accelerate")
            stdscr.addstr(4, 0, "s: Decelerate")
            stdscr.addstr(5, 0, "a: Steer left")
            stdscr.addstr(6, 0, "d: Steer right")
            stdscr.addstr(7, 0, "f: Forward")
            stdscr.addstr(8, 0, "r: Reverse")
            stdscr.addstr(9, 0, "m: Manual mode")
            stdscr.addstr(10, 0, "q: Quit")
            stdscr.addstr(12, 0, "Press key: ")

            key = stdscr.getch()
            stdscr.clrtoeol()

            if key == ord('w'):
                accel = min(1023, accel + 50)
                can.can_send("OBU", "accel_pedal", accel)
                stdscr.addstr(14, 0, f"Acceleration sent: {accel}     ")
            elif key == ord('s'):
                accel = max(0, accel - 50)
                can.can_send("OBU", "accel_pedal", accel)
                stdscr.addstr(14, 0, f"Deceleration sent: {accel}     ")
            elif key == ord('a'):
                steer = max(0, steer - 100)
                can.can_send("OBU", "steer_pos_set", steer)
                stdscr.addstr(14, 0, f"Steering left: {steer}         ")
            elif key == ord('d'):
                steer = min(1023, steer + 100)
                can.can_send("OBU", "steer_pos_set", steer)
                stdscr.addstr(14, 0, f"Steering right: {steer}        ")
            elif key == ord('f'):
                can.can_send("OBU", "bouton_on_off", 1)
                stdscr.addstr(14, 0, "Forward gear engaged         ")
            elif key == ord('r'):
                can.can_send("OBU", "bouton_on_off", 0)
                stdscr.addstr(14, 0, "Reverse gear engaged         ")
            elif key == ord('m'):
                can.can_send("OBU", "bouton_auto_manu", 1)
                stdscr.addstr(14, 0, "Manual mode activated        ")
            elif key == ord('q'):
                stdscr.addstr(16, 0, "Exiting...")
                break

            stdscr.refresh()
            time.sleep(0.05)

    except KeyboardInterrupt:
        stdscr.addstr(16, 0, "Keyboard interrupt received")
    finally:
        can.stop()
        stdscr.addstr(17, 0, "CAN interface closed.")
        stdscr.refresh()
        time.sleep(1)

if __name__ == "__main__":
    curses.wrapper(main)
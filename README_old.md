# control-vacop
## Overview of the document
This repository provides the implementation of a communication between a raspberryPi 4 and Solo Mega motors using the CANOpen protocol. 
This implementation is based on SoloPy library provided by SOLO Motor Controllers to control.
This code evolved to include the communication between two raspberryPi, one controlling the solo Mega motors and the other communicating the brake, steer values through a personalized can protocol.


## Features 
- 	OBU.py 
	DualMotorController.py
	MotorController.py
	MotorController_test.py
	
- Solo Motors configuration using Solo Motors terminal : SOLO-WorkSpace[2025-07-08_10-30].solows
	You can load this file using The motor terminal provided by Solo-FL to calibrate the motors.
	This file is specific to the motors used for the project. If you are not working with the same motors provided in this project, please refer to the following website : [https://www.solomotorcontrollers.com/blog/hall-sensors-to-solo-for-controlling-speed-torque-brushless-motor/]

## Configuration 
1. In RaspberryPi
	``` 	sudo nano /boot/config.txt ```
	In the file you either add or modify the following parameters
		dtparam=spi=on
		dtoverlay=mcp2515x ...
# Warning 
	This repository uses a modified version of SoloPy -- 2025.
	The modifications are : SoloPy/MCP2515.py can_transmit 
				if not information_received:
				    result = False
				    error = Error.GENERAL_ERROR
				    return result, error


## License

VACOP_control is released under the **MIT License**.

See `COPYING <COPYING>`_ for the full license text.

If you have any question or feedback please don't :)
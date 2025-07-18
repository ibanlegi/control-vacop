from abc import ABC, abstractmethod

class AbstractSensor(ABC):
    @abstractmethod
    def read(self) -> int:
        """Reads a raw value from the sensor."""
        pass

from abc import ABC, abstractmethod

class AbstractController(ABC):
    @abstractmethod
    def wait_for_start(self) -> bool:
        """
        Waits for a start signal to begin operation.

        This method should block until a 'start' signal or message is received.
        Returns True if the start command is successfully received, otherwise False.
        """
        pass

    @abstractmethod
    def initialize(self):
        """
        Initializes the controller before entering the main loop.

        Called immediately after receiving the start signal.
        Can be used to prepare system state, send initialization messages, etc.
        """
        pass

    @abstractmethod
    def update(self):
        """
        Updates the controller logic (main loop logic).

        Called repeatedly in the main control loop.
        Should handle periodic tasks such as reading sensor data,
        sending messages, or reacting to state changes.
        """
        pass
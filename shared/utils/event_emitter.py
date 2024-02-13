from collections import deque

"""
NOTE: We might not actually need a list of predefined events for the sake of ease of implementation. However it is nice
to see the list of all events available for each subclass of EventEmitter in its initializer. I decided to keep it as is.
"""


class EventEmitter:
    def __init__(self, events):
        self._listeners = {}
        for event in events:
            self._listeners[event] = deque()

    def emit(self, event: str, *args, **kwargs):
        """An internal method to dispatch events to registered listeners"""
        for listener in self._listeners[event]:
            listener(*args, **kwargs)

    def on(self, event: str, callback: callable):
        """
          Registers an event listener. Registering a duplicate event listener with the same callback is ignored.

          Raises:
            ValueError: If passing an invalid event
        """
        if event not in self._listeners:
            raise ValueError(f"Not a valid event: \"{event}\", sorry.")
        if callback in self._listeners[event]:
            # Show warning, maybe. For now silently don't do anything.
            pass
        else:
            self._listeners[event].append(callback)

    def off(self, event, callback):
        """
          Unregisters an event listener.

          Raises:
            ValueError: If passing an invalid event or if the listeners was not registered before.
        """

        if event not in self._listeners:
            raise ValueError(f"Not a valid event: \"{event}\", sorry.")

        try:
            self._listeners[event].remove(callback)
        except ValueError:
            raise ValueError("Cant unregister an event listener that has not been registered before, sorry.")

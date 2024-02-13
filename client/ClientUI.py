import asyncio
import logging
from prompt_toolkit import Application
from prompt_toolkit.shortcuts import input_dialog, message_dialog
from prompt_toolkit.application import in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea

from shared.utils.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class ClientUI(EventEmitter):
    """
      This class emits following events:
        - message_submit (message: str): Emitted, when a message was submitted from the UI.
    """

    def __init__(self):
        EventEmitter.__init__(self, events=["message_submit"])
        self.buffer_lock = asyncio.Lock()
        self.message_buffer = Buffer(name="Messages")

        root_container = HSplit([
            Window(content=BufferControl(buffer=self.message_buffer, focusable=False), wrap_lines=True),
            Window(height=1, char='-+'),
            TextArea(dont_extend_height=True, scrollbar=True, multiline=False,
                     accept_handler=lambda buf: self._on_buffer_submit(buf))
        ])

        layout = Layout(root_container)

        root_kb = KeyBindings()

        @root_kb.add('c-c')
        def exit_(_event):
            """ Pressing Ctrl-C will exit the user interface."""
            self.exit()

        self.app = Application(layout=layout, full_screen=True, key_bindings=root_kb)

    @staticmethod
    async def alert(*args, **kwargs):
        async with in_terminal():
            dialog_frontapp = message_dialog(*args, **kwargs)
            await dialog_frontapp.run_async()

    @staticmethod
    async def ask_for(*args, **kwargs):
        """
          Shows an input dialog and returns the result.

          KWArgs:
            title (str): Title of the dialog
            text (str): Text displayed
            default (str): Pre-filled value

          Raises:
            KeyboardInterrupt: If user wishes to close the app via ctrl + c signal.
        """
        async with in_terminal():
            kb = KeyBindings()

            @kb.add('c-c')
            def exit_(event):
                event.app.exit()

            dialog_frontapp = input_dialog(*args, **kwargs)
            dialog_frontapp.key_bindings = kb
            response = await dialog_frontapp.run_async()

            if response is None:
                raise KeyboardInterrupt

            return response

    async def draw(self):
        """
          Starts a rendering loop of the application UI. Blocks until the UI is exited.
        """
        try:
            await self.app.run_async()
        except asyncio.CancelledError:
            logger.debug("ClientUI canceled")
        finally:
            self.exit()

    def exit(self, err=None):
        """
          Stops the application UI.
        """
        if self.app.is_running:
            self.app.exit(err)

    async def display_text(self, text):
        """
          Display a new message in the textarea window
        """
        async with self.buffer_lock:
            self.message_buffer.text += text + "\n"

    def _on_buffer_submit(self, buf):
        """
          An internal helper method to process new message submits
        """
        if buf.text.strip() == "":
            return
        self.emit("message_submit", buf.text)

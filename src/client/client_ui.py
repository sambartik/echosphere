import asyncio
import logging
from prompt_toolkit import Application
from prompt_toolkit.shortcuts import input_dialog, message_dialog, set_title
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
    Handles the UI part of the client application which user directly interacts with.

    This class emits following events:
        - message_submit (message: str): Emitted, when a message was submitted from the UI.
    """

    def __init__(self, title: str):
        EventEmitter.__init__(self, events=["message_submit"])
        self.title = title
        self.buffer_lock = asyncio.Lock()
        self.message_buffer = Buffer(name="Messages", read_only=True)
        self.buffer_control = BufferControl(buffer=self.message_buffer)
        self.buffer_control_window = Window(
            self.buffer_control,
            wrap_lines=True
        )
        self.text_input = TextArea(dont_extend_height=True, scrollbar=True, multiline=False, accept_handler=lambda buf: self._on_buffer_submit(buf))

        # Here, we define the whole layout of the main chat window:
        root_container = HSplit([
            self.buffer_control_window,
            Window(height=1, char='-+'),
            self.text_input
        ])
        self.layout = Layout(root_container)
        self.layout.focus(self.text_input)

        root_kb = KeyBindings()

        @root_kb.add('c-c')
        def exit_(_event):
            """ Pressing Ctrl-C will exit the user interface."""
            logger.info("UI requested to be exited by the user.")
            self.exit()

        @root_kb.add('tab')
        def tab(_event):
            """ Pressing TAB will change the focus between text_input and buffer_control_window. """
            if self.layout.has_focus(self.text_input):
                self.layout.focus(self.buffer_control_window)
            else:
                self.layout.focus(self.text_input)

        self.app = Application(layout=self.layout, full_screen=True, key_bindings=root_kb)

    async def alert(self, text: str):
        """ Shows a message box with a text. """
        async with in_terminal():
            dialog_frontapp = message_dialog(title=self.title, text=text)
            await dialog_frontapp.run_async()

    async def ask_for(self, text: str, default: str = ""):
        """
        Shows an input dialog and returns the result.

        Parameters:
            text: The text displayed next to an input field.
            default: Prefilled value of the input field

        Raises:
            KeyboardInterrupt: If user wishes to close the app via ctrl + c signal.
        """
        async with in_terminal():
            kb = KeyBindings()

            @kb.add('c-c')
            def exit_(event):
                event.app.exit()

            dialog_frontapp = input_dialog(title=self.title, text=text, default=default)
            dialog_frontapp.key_bindings = kb
            response = await dialog_frontapp.run_async()

            if response is None:
                logger.info("Input dialog exited by the user.")
                raise KeyboardInterrupt

            return response

    async def draw(self):
        """ Starts a rendering loop of the application UI. Blocks until the UI is exited. """
        try:
            logger.info("Starting rendering loop...")
            await self.app.run_async()
        except asyncio.CancelledError:
            logger.debug("ClientUI draw task was canceled")
        finally:
            self.exit()

    def exit(self, err=None):
        """ Stops the application UI. """
        # Needed to check also for the internal future variable, because for some reason
        # the is_running was not enough to exit the UI safely. Received an exception in some edge cases.
        # More about their internal handling of exit: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/master/src/prompt_toolkit/application/application.py#L1292
        if self.app.is_running and not self.app.future.done():
            if err:
                logger.error(f"Stopping the application UI due to an error: {err}")
            else:
                logger.debug(f"Stopping the application UI gracefully.")
            self.app.exit(exception=err)

    async def display_text(self, text):
        """ Displays a new text at the end of textarea window """
        logger.debug(f'Displaying the text in the chat window.')
        async with self.buffer_lock:
            # Scrolls back to the latest messages
            self.message_buffer.cursor_position = len(self.message_buffer.text)

            # https://github.com/prompt-toolkit/python-prompt-toolkit/issues/540
            new_doc = self.message_buffer.document.insert_after(f"{text}\n")
            self.message_buffer.set_document(new_doc, bypass_readonly=True)

            self.buffer_control.move_cursor_down()

    def _on_buffer_submit(self, buf):
        """ An internal helper method to process new message submits """
        if buf.text.strip() == "":
            return

        logger.debug(f'Submitting a message.')
        self.emit("message_submit", buf.text)

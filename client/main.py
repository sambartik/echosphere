import logging
import os
import sys
import traceback

# Add the parent directory of the current script to sys.path
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
###################

import asyncio

from shared.validators import valid_username, valid_message
from shared.errors import NetworkError

from client.errors import ApplicationError, MessageError
from client.client_ui import ClientUI
from client.client_networking import ClientNetworking


class ClientApplication:
    """ An orchestrator for network communication with the server and the user through a UI. """

    def __init__(self, ui: ClientUI, networking: ClientNetworking):
        self.ui = ui
        self.networking = networking
        self.username = None

        # Register event listeners
        self.ui.on("message_submit", self.on_message_submit)
        self.networking.on("message_received", self.on_message_received)
        self.networking.on("connection_lost", self.on_connection_lost)

    def on_message_submit(self, message: str):
        if valid_message(message):
            logging.debug(f"User submitted a valid message.")
            asyncio.create_task(self.broadcast_message(message))
        else:
            logging.warning(f"User submitted an invalid message.")
            self.ui.alert("The message you were trying to send is invalid.")

    def on_message_received(self, username: str | None, message: str):
        if username is not None:
            logger.info(f"Received message from a user {username}.")
        else:
            logger.info(f"Received a system message!")
        asyncio.create_task(self.display_message(username, message))

    def on_connection_lost(self, err):
        logger.warning(f"Connection lost: {err}")
        asyncio.create_task(self.stop(err))

    async def run(self):
        """ Starts the application and blocks until it exits. """
        try:
            logger.info(f"Starting the client application...")
            username, host, port, server_password = await self._config_prompt()
            await self.networking.join_server(host, int(port), username, server_password)
            await self.ui.draw()
            await self.stop()
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.debug("The application was canceled.")
            await self.stop()
        except Exception as e:
            logger.error(f"Base exception caught in the run function: {type(e)}, {e}")
            logger.error(traceback.format_exc())
            await self.stop(e)

    async def _config_prompt(self):
        """
        Asks the user for connection configuration and then returns the results.

        Raises:
            KeyboardInterrupt: If one of the dialogs was interrupted

        Returns:
            A tuple: (username, host, port, server_password)
        """
        username = await self.ui.ask_for("Enter your username: ")
        while not valid_username(username):
            await self.ui.alert("Your username is invalid, it needs to be alphanumeric and 3 - 12 characters long.")
            username = await self.ui.ask_for("Enter your username: ")
        self.username = username
        host = await self.ui.ask_for("Enter server host: ", default="localhost")
        port = await self.ui.ask_for("Enter server port: ", default="12300")
        server_password = await self.ui.ask_for("Enter the server's password (leave empty for none): ", default="")

        return username, host, port, server_password

    async def stop(self, err=None):
        """
            Stops the client and if this call was triggered because of an error, it displays it to the user.

            Parameters:
                err: An error that triggered the stop call.
        """
        if err:
            logger.info(f"Stopping the application due to an error: {err}")
        else:
            logger.info(f"Stopping the application gracefully.")
        self.networking.disconnect()
        self.ui.exit()
        if err:
            await self.ui.alert(f"Well, something bad happened :(.\nError: {err}")

    async def display_message(self, username: str | None, message: str):
        """
        Displays the message sent by the user with username provided. System messages does not have sender's username, i.e.
        username is set to None.

        Parameters:
            username: The username of the sender. Special value None is reserved for system messages.
            message: The message
        """
        if not username:
            await self.ui.display_text(f"**SYSTEM**: {message}")
        else:
            await self.ui.display_text(f"<{username}>: {message}")

    async def broadcast_message(self, message: str):
        """ Receives the message from the UI and broadcasts it to other connected users. """
        try:
            logger.debug(f"Sending a message to the server: ({message})")
            await self.networking.send_message(message)
            await self.display_message(self.username, message)
        except NetworkError as err:
            logger.error(f"A network error occurred while sending a message to the server")
            logger.error(traceback.format_exc())
            await self.stop(err)
        except MessageError:
            logger.info("Message was rejected by the server.")
            await self.ui.alert(f"The message was rejected by the server, sorry.")


def configure_client_logging():
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = log_level_map.get(os.getenv('LOG_LEVEL'), logging.INFO)
    log_enabled = os.getenv('LOG_ENABLED', False)
    log_filepath = os.getenv("LOG_FILEPATH", "client.log")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%d-%m-%Y %H:%M:%S"

    if log_enabled:
        logging.basicConfig(level=log_level, format=log_format, datefmt=date_format,
                            handlers=[logging.FileHandler(log_filepath, encoding="utf-8", mode="a")])
    else:
        logging.disable()

async def main():
    try:
        ui = ClientUI("ChatClient")
        networking = ClientNetworking()
        app = ClientApplication(ui, networking)
        await app.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.debug("Main canceled")
    except ApplicationError as e:
        logger.error("Caught exception in the main function: ", type(e), e)
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    configure_client_logging()
    logger = logging.getLogger(__name__)
    asyncio.run(main())

import os
import sys
import logging

# Add the parent directory of the current script to sys.path
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
###################

import asyncio

from shared.utils.ConcurentTasksGroup import ConcurentTasksGroup
from shared.utils.logging_setup import configure_logging
from shared.validators import valid_username
from shared.errors import NetworkError

from client.errors import ApplicationError, MessageError
from client.ClientUI import ClientUI
from client.ClientNetworking import ClientNetworking


class ClientApplication:
  def __init__(self, ui: ClientUI, networking: ClientNetworking):
    self.ui = ui
    self.networking = networking
    self.username = None
    
    # Register event listeners
    self.ui.on("message_submit", lambda message: asyncio.create_task(self.broadcast_message(message)))
    self.networking.on("message_received", lambda username, message: asyncio.create_task(self.display_message(username, message)))
    self.networking.on("connection_lost", lambda err: asyncio.create_task(self.stop(err)))
  
  async def run(self):
    """ Starts the application and blocks until it exits. """
    try:
      username, host, port = await self._config_prompt()
      await self.networking.join_server(host, int(port), username)
      await self.ui.draw()
      logger.info("Reached the end of run method.")
      await self.stop()
    except (asyncio.CancelledError, KeyboardInterrupt):
      logger.info("Cancelling app")
      await self.stop()
    except Exception as e:
      logger.info(f"Base exception in the run function: {type(e)}, {e}")
      await self.stop(e)

  async def _config_prompt(self):
    """
      Asks the user for connection configuration and then returns the results.
      
      Raises:
        KeyboardInterrupt: If one of the dialogs was interrupted
      
      Returns:
        A tuple: (username, host, port)
    """
    title = "ChatClient"
    username = await self.ui.ask_for(title, text="Enter your username: ")
    while not valid_username(username):
      await self.ui.alert(title, text="Your username is invalid, it needs to be alphanumeric and 3 - 12 characters long.")
      username = await self.ui.ask_for(title, text="Enter your username: ")
    self.username = username
    host = await self.ui.ask_for(title, text="Enter server host: ", default="localhost")
    port = await self.ui.ask_for(title, text="Enter server port: ", default="12300")

    return username, host, port
    
  async def stop(self, err=None):
    """
      Stops the client and if this call was triggered because of an error, it displays it to the user.
      
      Parameters:
        err: An error that triggered the stop call.
    """
    logger.info(f"Stopping the application. (err: {err})")
    self.networking.disconnect()
    self.ui.exit()
    if err:
      await self.ui.alert(title="ChatClient", text=f"Well, something baad happend :(.\nError: {err}")

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
    """
      Receives the message from the UI and broadcasts it to other connected users.
    """
    logger.debug(f"Broadcasting a message: ({message})")
    try:
      await self.networking.send_message(message)
      await self.display_message(self.username, message)
    except NetworkError as err:
      await self.stop(err)
    except MessageError as err:
      await self.ui.alert(title="ChatClient", text=f"The message was rejected by the server, sorry.")
    
    
async def main():
  try:
    ui = ClientUI()
    networking = ClientNetworking()
    app = ClientApplication(ui, networking)
    await app.run()
  except (asyncio.CancelledError, KeyboardInterrupt):
    logger.info("Main canceled")
  except ApplicationError as e:
    logger.info("Caught exception at the end: ", type(e), e)

if __name__ == '__main__':
    configure_logging("client.log")
    logger = logging.getLogger(__name__)
    asyncio.run(main())
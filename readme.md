_This is course project for Programming 1 during the winter semester. This is purely educational only and should not be used in any production environments as it has serious security holes. Take a peak!_

# About the project
This project defines a custom designed binary protocol called [EchoSphere Chat Protocol](protocol.md) and alongside it includes implementation of a server and client applications supporting it.

The chat client is a python application that allows to communicate with others through a terminal window! It offers following features:
- Minimalistic terminal UI
- Effortless connectivity
- Password protected server
- User join/leave notifications
- Chat commands
- UTF-8 support* 🔥 😎 和平

_* needs to be supported by the user's terminal_

# User guide

The client allows users to connect to an external server hosting the EchoSphere server and provides a terminal UI to seamlessly interface with it.

### Installation steps
Before continuing, you need to have git and python v3 installed on your computer. Please, ensure that you do have them.

1. Clone the repository: 
```bash
git clone https://github.com/sambartik/echosphere
```
2. Get into the cloned directory:
```bash
cd echosphere
```
3. Install required dependencies:
```bash
pip install -r src/client/requirements.txt
```
4. Start the client:
```bash
python src/client/main.py
```

### Connecting to the server
It is really simple just as starting the client and filling out few data required to make a connection the server.

Immediately after the start a first screen pops up asking you for the username to be used during the session:

![A screen asking for input for username](images/username_screen.png)

You can type the username straight away and when you are done, hit the enter key to confirm the username and to change the focus to the "OK" and "Cancel" buttons bellow the input field. Button currently in the focus will be highlighted in red colour. Hitting the enter key for the second time will submit the username, otherwise you can change the focus of the button to "Cancel" in order to exit the application.

The username needs to be 3-12 characters long and can include ONLY alphanumerical characters. If the provided username is invalid, you wil be kindly informed by an error screen such as this:

![An error screen shown after entering invalid username](images/username_error_screen.png)

In an exactly the same way you will be prompted for other information: the server host, port and the server password. These information should be provided by your server administrator.

### Sending messages
Once you successfully join the server, other clients will be notified by a system message and you will be greeted with an empty chat window, because previous conversations stay hidden to newcomers:

![Am empty chat window](images/empty_chat_window.png)

You can start typing your message right away and submit it by hitting enter. The message must be at least 1 character long and at most 1000 characters long:

![Chat window with single user message](images/message_chat_window.png)

The server can reject a message based on its content policy, etc. In such case an error screen will be displayed.

### Scrolling through the history
Right after logging in, the focus will be on the text input field, indicated by a white rectangle - the cursor - in the bottom left corner. This means that you can start typing your message and eventually submit it to the server by clicking the ENTER key on the keyboard. The arrow keys up and down on the keyboard serve a special function: they "scrolls" through the message history you have sent. Clicking arrow up will bring old messages into the text field, giving you the possibility to edit it and send it again. The same applies with the arrow down, just the other way round.

You don't have to interact only with the input field. By tapping TAB key, you can toggle the focus to the messages window and view old messages that were sent on the server. It is also done in a similar fashion, using arrow keys in a similar fashion as in previous example to move the cursor up and down.


### Commands
Commands are sent by sending a special messages starting with `/`. For now, the server supports only following commands:
- `/list`
  - Lists the currently connected users
- `/ping`
  - No users connected? Bored with the human counterparts? Poke the server! It answers, too ;)

![Ping command showcase](images/ping_chat_command.png)

### Closing the application / disconnecting from the server
To disconnect from the server, simply close the application with the keyboard shortcut `CTRL + C`.

### Logging
Logging into a file can be configured via environmental variables:

| Name          | Description                                                | Possible values                                 | Default value  |
|---------------|------------------------------------------------------------|-------------------------------------------------|----------------|
| `LOG_ENABLED` | Turns on or off logging                                    | `TRUE`, `FALSE`                                 | `FALSE`        |
| `LOG_LEVEL`   | Defines the specificity of logs                            | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO`         |
| `LOG_FILE`    | Defines the filepath to the file where logs will be stored | Arbitrary filepath                              | `./client.log` |



# Server administrator guide
### Installation steps
Before continuing, you need to have git and python v3 installed on your computer. Please, ensure that you do have them.

1. Clone the repository: 
```bash
git clone https://github.com/sambartik/echosphere
```
2. Get into the cloned directory:
```bash
cd echosphere
```
3. Start the server (with default settings):
```bash
python src/server/main.py
```

### Configuration
The configuration of the server is done almost solely by passing arguments to the start command. Following arguments are accepted:
- Port: --port
  - default: 12300
- Server password: --password
  - default: None

Additionally, console logging can be configured via environmental variables:

| Name        | Description                     | Possible values                                 | Default value |
|-------------|---------------------------------|-------------------------------------------------|---------------|
| `LOG_LEVEL` | Defines the specificity of logs | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO`        |

For example, to start a server listening on port `13000` and protected with password `My_Password` you would:
```bash
python src/server/main.py --port 13000 --password My_Password
```

Server responses to `/ping` command can be configured by editing the `server/pong_messages.txt` file. Put each new response on a new line. 

_Disclaimer: The pong messages were generated by an AI as a demo._

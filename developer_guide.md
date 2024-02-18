# Who is this guide for?

This documentation is intended for developers that would like to get an initial grasp of the project's architecture and for those that would like to tinker and extend some of its functionalities.

# General design choices

The whole repository is modular and structured into 3 different packages: client, server and shared. Client package contains the code for the client application that users interact with. Similarly, the server package contains the code of the server. Shared package contains code shared between these two packages, that way it helps to keep the code DRY.

Because of tight dependence on network communication, python's asyncio is heavily used throughout the code. The inter-class communication is mostly done by emitting events and subsequently listening for them in different classes.

It was planned out with extensibility of core features in mind, providing a hassle-free way to define new packet types, responses, commands...

# Shared package

Common exceptions used both by server and client are defined in `errors.py`. 

As the name suggests, `validators.py` contains code that checks the validity of data required to be in a specific format by the protocol, such as the username.

The task of handling incoming and outgoing network data and the translation from bytes to Packet objects and vice versa is handled entirely by a subclass of `asyncio.Protocol` (more about transports & protocols at [python's docs page](https://docs.python.org/3/library/asyncio-protocol.html#transports-and-protocols)). The subclass is defined in `chat_protocol.py`

The shared package is further subdivided into utils and packets subpackages:

### Packets subpackage

This essentially describes the whole protocol and makes it possible to work with packets in an object-oriented way. There is a `Packet` class defined in `base_packet.py` and all packet types have their own class that is a subclass of `Packet` - all the subclasses reside in `definitions.py`.

Enums PacketType and ResponseCode are defined in `types.py` and have the same values as specified in the [protocol specification](protocol.md).

Packet factory function is in `factory.py` that extracts the first packet from a blob of binary data. It utilizes the common interface defined by `Packet` and internally also depends on a map, which maps between a concrete PacketType and corresponding Packet subclass.

### Utils subpackage

Contains code that is not related to the protocol or anything directly related with the project. It defines helpful tools, such an example is the `EventEmitter` that is facilitated in the inter-class communication.

# Server package

Errors used only by the server side are defined in `errors.py`.

### ServerNetworking

The low-level server networking is implemented by `ServerNetworking` class in `server_networking.py` module. It handles things such as accepting TCP connections from clients, managing the communication on packet level (the binary level is already abstracted thanks to `chat_protocol.py`).
There are packet handlers (subclasses of `PacketHandler`) in `packet_handlers.py` that abstract the logic of packet handling based on their packet type out of `ServerNetworking` class. As a result it achieved better separation of concerns.

### Entrypoint

The entrypoint of the server application is in `main.py`. The significant part of that module takes up the class `ServerApplication`, that implements the actual application logic such as handling user joins, user leaves, messages. It gets data from `ServerNetworking` via events. Similarly, it also handles commands (special messages for the server) via command handlers in `command_handlers.py`.

# Client package

Errors used only by the client side are defined in `errors.py`.

The client is made out of 2 very distinct parts: UI and networking.

### ClientUI

Class `ClientUI` in `client_ui.py` is responsible for the whole terminal UI. It uses the `prompt_toolkit` library, which allows for cross-platform support. In order to make changes in the UI, the knowledge of this library is very much needed. The docs are available [here](https://python-prompt-toolkit.readthedocs.io/en/3.0.43/).

The UI of the window with chat and message input is described in the initializer of `ClientUI` by `root_container` and `layout`.

Other than that, the ClientUI provides methods for displaying a text message popup via the `alert` method and also for asking the user for input via `ask_for` method.

### ClientNetworking

It handles all the communication with the server, in particular: handles login, logout, sending/receiving messages, heartbeats. It handles all the communication on packet level.

It furthers abstracts the idea of packets and emits events: `message_received`, `connection_lost`.

### Entrypoint

The main portion of the entrypoint `main.py` module is the `ClientApplication` class that acts as an orchestrator between the UI and networking. The `start` method is responsible for starting and running the whole application, it uses `ClientUI` and `ClientNetworking` to do so.


# Additional info:

## Adding a new packet

To add a new packet, it is required to update the protocol specification first. When that is done, the new protocol type is added into the PacketType enum in `shared/packets/types.py`. The numbers assigned to the enums must be the same as in the protocol specification. 

After that, a new Packet subclass must be defined and registered in `shared/packets/definitions.py`, for example:
```python
@register_packet(PacketType.LOGOUT)
class LogoutPacket(Packet):
    MAX_PAYLOAD_LENGTH = 0

    def __init__(self):
        super().__init__(b'')

    @classmethod
    def _from_payload(cls, _payload):
        return cls()
```
_Notice:_ the packet subclass needs to be registered via the `@register_packet` class decorator.

Each packet defines its own limit on max payload length (in bytes). In the initializer, it must call the super class initializer with the binary payload as first argument. Then, it needs to implement method `_from_payload` which returns an instance of the subclass based on the payload provided. 

In case of an invalid data, both `__init__` and `_from_payload` can raise an exception `shared.errors.InvalidPayloadError`.

## Sending/receiving packets
Sending packets is done through an instance of `shared.ChatProtocol`, which defines methods `send_packet` for sending packets without waiting for response and `send_packet_and_wait`, which waits for the next packet received and returns it.

The `ChatProtocol` class defines among others event `packet_received` which allows to react every time a new packet is received.

## Packet handling on the server

Packets received by the server are handled by an appropriate packet handler. There can be at most 1 packet handler defined for each packet type. 

Definitions for them are located in `server/packet_handlers.py` module. Here is an example of a class that handles heartbeat packets:
```python
@register_packet_handler(PacketType.HEARTBEAT)
class HeartbeatPacketHandler(PacketHandler):
    def handle_packet(self, protocol: ChatProtocol, packet: HeartbeatPacket):
        self.networking.connections[protocol].last_heartbeat = datetime.now()
```

_Notice:_ Packet handler needs to be registered via `@register_packet_handler` class decorator.

`handle_packet` is the only method mandatory method to be implemented by packet handler classes. Each subclass has access to the instance of `ServerNetworking` class via its property: `self.networking`.

## Packet handling on the client

Clients listen for `packet_received` event and only react to message packets. Receiving the response packets is handled by the aforementioned `send_packet_and_wait` method of `shared.ChatProtocol`.

The code for message packet handling is in `on_new_packet` method of `ClientNetworking`.

## Commands

The command handling is entirely handled by the server. From user's perspective sending a command is as sending a typical message.

The command handling is defined in a similar fashion as packet handling, for example this is a handler for `/list` command:

```python
@register_command_handler("list")
class ListCommandHandler(CommandHandler):
    def handle_command(self, sender: str, args: list[str]):
        response_message = f"Connected users: {', '.join(self.server.connected_users.keys())}"
        self.server.send_message_to(None, sender, response_message)
```
_Notice:_ Command handler needs to be registered via `@register_command_handler` class decorator.

The subclasses are only required to implement the `handle_command` method. Each command handler has access to an instance of `ServerApplication` via its property: `self.server`.

# Vision into the future:
As I implemented the server I learned a lot, and it was pretty much hands-on experience. I could see changing the packets to include so-called correlation number to be able to match request packets to response packets. That would be a great help when sending multiple request packets at the same time. Currently, only a single request packet can be sent and it blocks other request packets until the response for the first packet arrives.

Also, having a more rigid client packet handling of incoming packets, similar to server's would also be nice, in case the protocol gets more evolved.
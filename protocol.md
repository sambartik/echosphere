# EchoSphere Chat Protocol
The EchoSphere Chat Protocol, version 1 (ESCP in short) is a simple binary protocol designed for client/server chat applications and uses TCP as its transport layer. The endianity of all multibyte data is Big-Endian. It has fixed header length of 4 bytes and a variable length payload.

# The general packet structure:
```
+----------+----------+--------------+----------------------------------------+
| 1 byte   | 1 byte   |   2 bytes    |              N bytes                   |
|----------|----------|--------------|----------------------------------------|
| Version  | Type     | Payload Len  |                Payload                 |
+----------+----------+--------------+----------------------------------------+
```

The header consists of 3 fields in the following order: protocol version, packet type, payload length. The protocol version is an unsigned number that helps with identifying a newer versions of this protocol in the future. For now, the only acceptable protocol version is 1. Newer versions do not guarantee backwards compatibility! The packet type field is also an unsigned number and it distinguishes between different kinds of packets (more in the packet types section). The payload length is an unsigned number of bytes of payload that follows the header.

The payload is a sequence of bytes that are interpreted differently based on the packet type specified in the header. Currently, the maximum length of any payload is 4096 bytes. Each packet type can subsequently define this limit to be lower. A packet can also have a payload length of 0, effectively having a packet without any payload. Such an example is the Heartbeat packet.

In case server or client receives a packet with invalid type or packet that exceeds respective max. payload length or packet with a mismatched protocol version, it immediately closes the connection.

# Categorization of packets
All packets can be categorized into 3 distinct categories based on their interaction model and purpose within the protocol:

1. Request packets
When either the client or server sends a request packet, that side of the communication that sent it must wait for an appropriate response packet until they can send another request packet.
2. Response packets
These types of packets are sent as a response to an appropriate request packet that was received. In the current protocol version, there is only a single response packet type to every request packet and that is the Response packet (more in packet types section).
3. Meta packets
They serve as a spontanious information that was not requested and therefore does not need to be responded to. An example of such packet is the Heartbeat packet.

# Packet Types
The protocol defines a set of different packet types, which determines how will be the payload handled and parsed.

Based on their Packet Type unsigned number the ordered list is as follows:
## 1. Heartbeat packet (meta packet)
The heartbeat packet is sent continuously by the client after a successful login to a server. The time between two consecutive heartbeat packets should not be longer than 15 seconds, otherwise the server will consider such connection as stale and closes the connection with the client and informs other users by sending a message as if the user left the server.

```
+--------+---------+--------------+
| 0x01   | 0x01    | 0x0000       |
+--------+---------+--------------+
Type: 1
Max Payload Len: 0
```

## 2. Login packet (request packet)
The login packet is sent by the client after a successful estabilisment of a TCP connection with the server. It acts as an introduction of a client to the server and includes required information for the server such as the client's username and the password to the server.

```
+--------+---------+--------------+------------------------------+
| 0x01   | 0x02    | Payload Len  |  Username + Password (UTF-8) |
+--------+---------+--------------+------------------------------+
Type: 2
Max Payload Len: 256 bytes
```

The payload is an UTF-8 string that consists of client's username and a server's password, separated by the character `"|"`.
The username must be at least 3 characters long and at most 12 characters long. It can only includes alphanumeric characters.
The server's password length can range from 0 to 48 characters. If the server's password is 0, then it has no password set. All characters are permited.

Payload format: `"<username>|<password>"`. In case logging into a server that has not set a password, then the payload would look like: `"<username>|"`.

Server responds to this packet by sending a Response packet with the response code:
   - 1: In case the username is not in a valid format.
   - 2: In case there is already a user connected with the same username.
   - 4: In case the password is incorrect
   - 0: When the login was successful

## 3. Message packet (request/meta packet)
The purpose of this packet is to deliver messages between communication parties. Both server and client send this type of packet. However, when the client sends this packet, it is considered to be a request packet and therefore the client must wait for a response. This allows the server to reject some of the client messages because of formating issues, etc.
In the other case, when server is sending this packet, it is considered to be a meta packet and clients that receive it do not respond to it, but rather display it in client's UI.

```
+--------+---------+--------------+------------------------------------------ +
| 0x01   | 0x03    | Payload Len  | Sender username + Message (UTF-8 encoded) |
+--------+---------+--------------+-------------------------------------------+
Type: 3
Max Payload Len: 4096
```

The payload is an UTF-8 encoded string in the following format: `"<sender's username>|<message>"`. The message needs to be at least 1 and at most 1000 characters long.

There are 2 types of messages:
   - User messages - These are sent by user to be received by other clients
   - System messages - Sent by the server to a single client or multiple clients (for example a notification when a user leaves)

System messages have empty sender's username part of the message and thus look like this: `"|<system message>"`.

When a client is sending a message, then it is considered to be a request packet and the server responds with a Response packet with following response codes:
   - 3: In case the server rejects the message for various reasons.
   - 0: Server accepts the message


## 4. Response packet (response packet)
This packet is sent only after receiving a request packet. This is the sole response packet currently specified in the protocol specification.

```
+--------+---------+--------------+----------------+
| 0x01   | 0x04    | Payload Len  | Response Code  |
+--------+---------+--------------+----------------+
Max Payload Len: 1 byte
```

Different kinds of responses are distinguished based on the response code which is a 1 byte unsigned number in the packet's payload

### Valid response codes:

| Response Code | Meaning           | Description                                                               |
|---------------|-------------------|---------------------------------------------------------------------------|
| 0             | OK                | The request was valid, there were no issues                               |
| 1             | INVALID_USERNAME  | The provided username is invalid (formatting, etc)                        |
| 2             | TAKEN_USERNAME    | The username is being used by another user                                |
| 3             | INVALID_MESSAGE   | The message format is invalid or breaches content rules of the server     |
| 4             | WRONG_PASSWORD    | The provided password for the server is incorrect                         |
| 5             | GENERIC_ERROR     | An unexpected error occured, which is not covered by other codes          |

## 5. Logout packet (meta packet)
Sent only by the clients to indicate to the server that the user is leaving and soon will close the connection as well.

```
+--------+---------+--------------+
| 0x01   | 0x05    | 0x0000       |
+--------+---------+--------------+
Max Payload Len: 0 byte
```

# Example connection flow
1. Client initiates TCP connection to the server.
2. Client logs in by sending a Login packet with their username and the server's password
3. Server responds with a Response packet with an appropriate response code.
4. Client starts sending Heartbeat packets every 15 seconds or less to maintain its connection to the server.
5. Client sends a message via Message packet, including its username as sender's username.
6. Servers responds to the packet sent by the client with a Response packet with an appropriate response code.
7. Server sends Message packets to one or more clients.
8. Client decides to leave the server and sends Logout packet.
9. Client closes the TCP connection.

# Other information
When a user joins or leaves the server, the server must send a system message to all of the other clients notifying them of such an event. Most of the time, user messages sent to the server will be broadcaster to all other clients, however the server may handle special types of messages as commands and may consequently send a system message to one or more clients, however that is not part of the specification.
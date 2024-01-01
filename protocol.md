The BS Chat Protocol v1 Packet Structure:
  Byte order: Big-Endian
  
  +----------+----------+--------------+----------------------------------------+
  | 1 byte   | 1 byte   |   2 bytes    |              N bytes                   |
  |----------|----------|--------------|----------------------------------------|
  | Version  | Type     | Payload Len  |                Payload                 |
  +----------+----------+--------------+----------------------------------------+
  Note: Max payload length out of all packet types is 4096 bytes <=> max size of any packet is 5000 bytes.

Packet Types:
1. HEARTBEAT
   +--------+---------+--------------+
   | 0x01   | 0x01    | 0x0000       |
   +--------+---------+--------------+
   Note: No payload, Payload Len = 0 bytes

2. LOGIN
   +--------+---------+--------------+---------------------------+
   | 0x01   | 0x02    | Payload Len  |  Username (UTF-8 encoded) |
   +--------+---------+--------------+---------------------------+
   Max Payload Len: 256 bytes

3. MESSAGE
   +--------+---------+--------------+------------------------------------------ +
   | 0x01   | 0x03    | Payload Len  | Sender username + Message (UTF-8 encoded) |
   +--------+---------+--------------+-------------------------------------------+
   Max Payload Len: 4096 bytes
   The payload is a single UTF-8 encoded string that includes senders username, delimiter and a message.
   Thus it looks like this: "<username>|<message>", where "|" is the delimiter and should not be part of username nor message.

4. RESPONSE
   +--------+---------+--------------+----------------+
   | 0x01   | 0x04    | Payload Len  | Response Code  |
   +--------+---------+--------------+----------------+
   Max Payload Len: 1 byte

5. LOGOUT
   +--------+---------+--------------+
   | 0x01   | 0x05    | 0x0000       |
   +--------+---------+--------------+
   Note: No payload, Payload Len = 0 bytes

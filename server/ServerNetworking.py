import asyncio
from datetime import datetime

from shared.chat_protocol import ChatProtocol
from shared.utils.event_emitter import EventEmitter
from shared.validators import valid_message, valid_username
from shared.packets.definitions import *

class Connection:
  def __init__(self, protocol, username=None):
    self.protocol = protocol
    self.username = username
    self.last_heartbeat = None

class ServerNetworking(EventEmitter):
  def __init__(self):
    EventEmitter.__init__(self, events=["user_joined", "user_left", "message_received"])
    self.listening = asyncio.get_running_loop().create_future()
    self.server = None
    self.connections = {}

  def username_is_taken(self, username: str):
    for connection in self.connections.values():
      if connection.username == username:
        return True
    return False

  def on_new_packet(self, protocol: ChatProtocol, packet: Packet):
    print("SERVER: New packet: ", packet)
    
    if isinstance(packet, LoginPacket):
      if not valid_username(packet.username):
        return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_USERNAME))
      
      if self.username_is_taken(packet.username):
        return protocol.send_packet(ResponsePacket(ResponseCode.TAKEN_USERNAME))
      
      protocol.send_packet(ResponsePacket(ResponseCode.OK))
      self.connections[protocol].username = packet.username
      self.emit("user_joined", protocol, packet.username)
      return
    
    elif isinstance(packet, MessagePacket):
      # Get the sender's username based on the their protocol instance. (each connection has its own)
      sender_username = self.connections[protocol].username
      if not valid_message(packet.message) or sender_username is None:
        return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_MESSAGE))
      
      protocol.send_packet(ResponsePacket(ResponseCode.OK))
      return self.emit("message_received", sender_username, packet.message)
    
    elif isinstance(packet, HeartbeatPacket):
      self.connections[protocol].last_heartbeat = datetime.now()
  
  def on_new_connection(self, protocol: ChatProtocol):
    print("SERVER: New connection!")
    self.connections[protocol] = Connection(protocol)
  
  def on_connection_close(self, protocol: ChatProtocol, err: Exception):
    print(f"SERVER: Connection closed (err: {err})")
    if self.connections[protocol].username:
      self.emit("user_left", protocol, self.connections[protocol].username, err)
    del self.connections[protocol]
  
  def accept_connection(self) -> ChatProtocol:
    protocol = ChatProtocol()
    protocol.on("connection_made", self.on_new_connection)
    protocol.on("packet_received", self.on_new_packet)
    protocol.on("connection_lost", self.on_connection_close)
    return protocol
  
  async def serve(self, host: str, port: int):
    if self.server:
      raise Exception("Server is already running!")
    
    self.server = await asyncio.get_event_loop().create_server(self.accept_connection, host, port)
    
    await self.server.serve_forever()
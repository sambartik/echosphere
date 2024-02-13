import re

def valid_username(username: str) -> bool:
  return (3 <= len(username) <= 12) and re.fullmatch(r'[a-zA-Z0-9]+', username)

def valid_message(message: str) -> bool:
  return 1 <= len(message) <= 1000

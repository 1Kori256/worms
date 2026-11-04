"""Length-prefixed JSON messages; TCP reads may split or combine packets."""

import json
import struct

MAX_MESSAGE = 128 * 1024


def receive_exact(connection, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = connection.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("Connection closed")
        chunks.extend(chunk)
    return bytes(chunks)


def receive_message(connection):
    size, = struct.unpack("!I", receive_exact(connection, 4))
    if not 0 < size <= MAX_MESSAGE:
        raise ValueError("Invalid message size")
    message = json.loads(receive_exact(connection, size))
    if not isinstance(message, dict):
        raise ValueError("Expected a JSON object")
    return message


def send_message(connection, message):
    data = json.dumps(message, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(data) > MAX_MESSAGE:
        raise ValueError("Message too large")
    connection.sendall(struct.pack("!I", len(data)) + data)

import struct
import unittest
from scripts.protocol import MAX_MESSAGE, receive_message, send_message


class Stream:
    def __init__(self, data=b"", chunk=10**9):
        self.data = bytearray(data)
        self.chunk = chunk

    def sendall(self, data):
        self.data.extend(data)

    def recv(self, size):
        size = min(size, self.chunk, len(self.data))
        result = bytes(self.data[:size])
        del self.data[:size]
        return result


class ProtocolTests(unittest.TestCase):
    def test_one_byte_reads_and_combined_messages(self):
        stream = Stream(chunk=1)
        send_message(stream, {"message": "Červy"})
        send_message(stream, {"player": 3})
        self.assertEqual(receive_message(stream), {"message": "Červy"})
        self.assertEqual(receive_message(stream), {"player": 3})

    def test_large_state_exceeds_old_receive_buffer(self):
        state = {"worms": [[[x, y] for x in range(30) for y in range(30)]] * 4}
        stream = Stream(chunk=127)
        send_message(stream, state)
        self.assertGreater(len(stream.data), 8192)
        self.assertEqual(receive_message(stream), state)

    def test_closed_or_truncated_connection(self):
        for data in (b"", b"\x00\x00", struct.pack("!I", 10) + b"{}"):
            with self.subTest(data=data), self.assertRaises(ConnectionError):
                receive_message(Stream(data))

    def test_invalid_length(self):
        for size in (0, MAX_MESSAGE + 1, 2**32 - 1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                receive_message(Stream(struct.pack("!I", size)))

    def test_malformed_or_nonobject_json(self):
        for payload in (b"pickle", b"[]", b"null", b"\xff"):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                receive_message(Stream(struct.pack("!I", len(payload)) + payload))

    def test_oversized_send_is_rejected(self):
        with self.assertRaises(ValueError):
            send_message(Stream(), {"text": "x" * MAX_MESSAGE})

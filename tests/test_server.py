import socket
import threading
import unittest
from types import SimpleNamespace
from server import GameServer
from scripts.network import Network
from scripts.protocol import send_message, receive_message


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = GameServer()
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen()
        self.clients = []
        self.threads = []
        self.app = SimpleNamespace(config={"server": {"ip": "127.0.0.1"}})

    def connect(self):
        def accept():
            connection, address = self.listener.accept()
            self.server.handle_client(connection, address)
        thread = threading.Thread(target=accept, daemon=True)
        thread.start()
        self.threads.append(thread)
        client = Network(self.app, port=self.listener.getsockname()[1])
        self.clients.append(client)
        return client

    def disconnect(self, client):
        index = self.clients.index(client)
        client.close()
        self.threads[index].join(timeout=2)
        self.assertFalse(self.threads[index].is_alive())

    def tearDown(self):
        for client in self.clients:
            client.close()
        for thread in self.threads:
            thread.join(timeout=2)
        self.listener.close()

    def test_four_players_and_fifth_in_new_room(self):
        clients = [self.connect() for _ in range(5)]
        states = [client.send() for client in clients]
        self.assertEqual([client.player for client in clients], [0, 1, 2, 3, 0])
        self.assertEqual([state.id for state in states], [0, 0, 0, 0, 1])
        self.assertEqual(states[0].active_players, 4)
        self.assertEqual(states[4].active_players, 1)

    def test_started_room_not_reset_by_new_connection(self):
        first = self.connect()
        before = first.send(ready=True)
        second = self.connect()
        self.assertNotEqual(second.send().id, before.id)
        self.assertTrue(first.send().started)

    def test_disconnect_keeps_room_and_other_player(self):
        first, second = self.connect(), self.connect()
        self.disconnect(first)
        state = second.send()
        self.assertEqual(state.connected, [False, True])
        self.assertEqual(state.worms[0], [])
        third = self.connect()
        self.assertEqual(third.player, 0)
        self.assertEqual(second.send().connected, [True, True])
        self.assertEqual(second.player, 1)

    def test_empty_room_removed_and_room_ids_never_reused(self):
        first = self.connect()
        old_id = first.send().id
        self.disconnect(first)
        self.assertEqual(self.server.games, {})
        second = self.connect()
        self.assertGreater(second.send().id, old_id)

    def test_bad_command_disconnects_only_sender(self):
        first, second = self.connect(), self.connect()
        send_message(first.client, {"type": "input", "direction": ["bad", 0]})
        with self.assertRaises(ConnectionError):
            receive_message(first.client)
        self.threads[0].join(timeout=2)
        self.assertEqual(second.send().connected, [False, True])


if __name__ == "__main__":
    unittest.main()

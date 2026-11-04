"""Run a local or LAN server without opening a Pygame window."""

import argparse
import copy
import logging
import socket
import threading

from scripts.game_instance import GameInstance
from scripts.protocol import receive_message, send_message


class GameServer:
    def __init__(self):
        self.games = {}
        self.lock = threading.Lock()
        self.next_id = 0

    def join(self):
        with self.lock:
            for game in self.games.values():
                if not game.started and sum(game.connected) < 4:
                    return game, game.add_player()
            game = GameInstance(self.next_id)
            self.next_id += 1
            self.games[game.id] = game
            return game, game.add_player()

    def handle_client(self, connection, address):
        game = None
        try:
            connection.settimeout(10)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            game, player = self.join()
            send_message(connection, {"player": player})
            logging.info("%s joined room %s as player %s", address, game.id, player + 1)
            while True:
                message = receive_message(connection)
                if message.get("type") != "input":
                    raise ValueError("Unknown command")
                direction = message.get("direction")
                if direction is not None and (
                    not isinstance(direction, list) or len(direction) != 2
                    or any(type(value) is not int for value in direction)
                    or tuple(direction) not in ((0, -1), (0, 1), (1, 0), (-1, 0))
                ):
                    raise ValueError("Invalid direction")
                with self.lock:
                    game.update()
                    if message.get("ready") is True:
                        game.ready()
                    if direction is not None:
                        game.turn(player, direction)
                    state = copy.deepcopy(game.snapshot())
                send_message(connection, state)
        except (OSError, ValueError, ConnectionError) as error:
            logging.info("%s disconnected: %s", address, error)
        finally:
            if game is not None:
                with self.lock:
                    game.disconnect(player)
                    if game.empty:
                        self.games.pop(game.id, None)
            connection.close()

    def serve(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((host, port))
            listener.listen()
            logging.info("Listening on %s:%s", host, listener.getsockname()[1])
            while True:
                connection, address = listener.accept()
                threading.Thread(target=self.handle_client,
                                 args=(connection, address), daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", nargs="?", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        GameServer().serve(args.host, args.port)
    except KeyboardInterrupt:
        pass
    except OSError as error:
        parser.exit(1, f"Server error: {error}\n")


if __name__ == "__main__":
    main()

import json
import socket
import threading
from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable

from steam_analysis.app.DistributionEntities.messages.types import MessageType


class Node(ABC):

    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 5000):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers: Dict[str, Dict] = {}  # {node_id: {"host": host, "port": port}}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.running = False
        self.server_thread: Optional[threading.Thread] = None

        # Регистрируем стандартные обработчики
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Регистрация обработчиков по умолчанию"""
        self.register_handler(MessageType.PING, self._handle_ping)
        self.register_handler(MessageType.STATUS, self._handle_status)

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Регистрация обработчика сообщений"""
        self.message_handlers[message_type] = handler

    def start(self):
        """Запуск узла"""
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"Node {self.node_id} started on {self.host}:{self.port}")

    def stop(self):
        """Остановка узла"""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=5)

    def _run_server(self):
        """Запуск TCP сервера"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)

            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Server error: {e}")
                    break

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Обработка входящего соединения"""
        try:
            data = client_socket.recv(4096)
            if data:
                message = json.loads(data.decode('utf-8'))
                self._process_message(message, client_socket)
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def _process_message(self, message: Dict, response_socket: socket.socket = None):
        """Обработка входящего сообщения"""
        try:
            msg_type = MessageType(message.get("type"))
            handler = self.message_handlers.get(msg_type)

            if handler:
                response = handler(message.get("data", {}))
                if response_socket and response:
                    response_socket.send(json.dumps(response).encode('utf-8'))
            else:
                print(f"No handler for message type: {msg_type}")

        except ValueError:
            print(f"Unknown message type: {message.get('type')}")
        except Exception as e:
            print(f"Error processing message: {e}")
            if response_socket:
                error_response = {
                    "type": MessageType.ERROR.value,
                    "data": {"error": str(e)}
                }
                response_socket.send(json.dumps(error_response).encode('utf-8'))

    def send_message(self, target_host: str, target_port: int, message: Dict) -> Optional[Dict]:
        """Отправка сообщения другому узлу"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((target_host, target_port))
                sock.send(json.dumps(message).encode('utf-8'))

                # Ждем ответ
                response_data = sock.recv(4096)
                if response_data:
                    return json.loads(response_data.decode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {target_host}:{target_port}: {e}")
        return None

    def broadcast(self, message: Dict):
        """Отправка сообщения всем пирам"""
        for peer_id, peer_info in self.peers.items():
            if peer_id != self.node_id:
                self.send_message(peer_info["host"], peer_info["port"], message)

    def add_peer(self, node_id: str, host: str, port: int):
        """Добавление узла в список известных"""
        self.peers[node_id] = {"host": host, "port": port}

    # Стандартные обработчики
    def _handle_ping(self, data: Dict) -> Dict:
        return {
            "type": MessageType.STATUS.value,
            "data": {"status": "alive", "node_id": self.node_id}
        }

    def _handle_status(self, data: Dict) -> Dict:
        return {
            "type": MessageType.STATUS.value,
            "data": {
                "node_id": self.node_id,
                "status": "running",
                "peers": len(self.peers)
            }
        }

    @abstractmethod
    def process_task(self, task_data: Dict) -> Dict:
        """Обработка задачи - должен быть реализован в подклассах"""
        pass
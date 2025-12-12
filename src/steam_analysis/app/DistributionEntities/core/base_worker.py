from .node import Node, MessageType
from typing import Dict, Any
from abc import abstractmethod


class BaseWorker(Node):
    """Базовый класс для всех воркеров"""

    def __init__(self, node_id: str, master_host: str, master_port: int,
                 host: str = "0.0.0.0", port: int = 5001):
        super().__init__(node_id, host, port)
        self.master_host = master_host
        self.master_port = master_port
        self.task_queue = []

        # Регистрируем обработчики задач
        self.register_handler(MessageType.TASK, self._handle_task)

    def start(self):
        """Запуск воркера с регистрацией на мастере"""
        super().start()
        self._register_with_master()

    def _register_with_master(self):
        """Регистрация на мастер-узле"""
        register_message = {
            "type": MessageType.REGISTER.value,
            "data": {
                "node_id": self.node_id,
                "host": self.host,
                "port": self.port,
                "worker_type": self.__class__.__name__
            }
        }

        response = self.send_message(self.master_host, self.master_port, register_message)
        if response:
            print(f"Worker {self.node_id} registered with master")

    def _handle_task(self, task_data: Dict) -> Dict:
        """Обработка входящей задачи"""
        try:
            result = self.process_task(task_data)
            return {
                "type": MessageType.RESULT.value,
                "data": {
                    "task_id": task_data.get("task_id"),
                    "result": result,
                    "worker_id": self.node_id
                }
            }
        except Exception as e:
            return {
                "type": MessageType.ERROR.value,
                "data": {
                    "task_id": task_data.get("task_id"),
                    "error": str(e),
                    "worker_id": self.node_id
                }
            }

    @abstractmethod
    def process_task(self, task_data: Dict) -> Dict:
        """Обработка конкретной задачи - реализуется в подклассах"""
        pass
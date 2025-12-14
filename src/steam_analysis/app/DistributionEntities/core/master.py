# steam_analysis/app/DistributionEntities/master_node.py
from .node import Node, MessageType
from typing import Dict, List, Optional
import threading
from collections import deque


class MasterNode(Node):
    """Мастер-узел, управляющий распределенной системой"""

    def process_task(self, task_data: Dict) -> Dict:
        pass

    def __init__(self, node_id: str = "master", host: str = "0.0.0.0", port: int = 5000):
        super().__init__(node_id, host, port)

        # Словари для управления воркерами
        self.workers: Dict[str, Dict] = {}  # {worker_id: {"host": host, "port": port, "type": type}}
        self.worker_types: Dict[str, List[str]] = {}  # {worker_type: [worker_id1, worker_id2]}
        self.task_queue = deque()
        self.task_results: Dict[str, Dict] = {}  # {task_id: result}
        self.pending_tasks: Dict[str, str] = {}  # {task_id: worker_id}

        # Регистрируем обработчики
        self.register_handler(MessageType.REGISTER, self._handle_register)
        self.register_handler(MessageType.RESULT, self._handle_result)

        # Запускаем диспетчер задач
        self.dispatcher_thread = threading.Thread(target=self._dispatch_tasks, daemon=True)

    def start(self):
        """Запуск мастера"""
        super().start()
        self.dispatcher_thread.start()
        print(f"Master node started. Ready to accept workers.")

    def _handle_register(self, data: Dict) -> Dict:
        """Обработка регистрации воркеров"""
        worker_id = data["node_id"]
        worker_type = data.get("worker_type", "unknown")

        self.workers[worker_id] = {
            "host": data["host"],
            "port": data["port"],
            "type": worker_type
        }

        if worker_type not in self.worker_types:
            self.worker_types[worker_type] = []

        if worker_id not in self.worker_types[worker_type]:
            self.worker_types[worker_type].append(worker_id)

        print(f"Worker registered: {worker_id} ({worker_type})")
        return {
            "type": MessageType.STATUS.value,
            "data": {"status": "registered", "master_id": self.node_id}
        }

    def _handle_result(self, data: Dict) -> Dict:
        """Обработка результатов от воркеров"""
        task_id = data["task_id"]
        worker_id = data["worker_id"]

        if task_id in self.pending_tasks:
            # Сохраняем результат
            self.task_results[task_id] = data.get("result", {})

            # Освобождаем воркер
            del self.pending_tasks[task_id]

            print(f"Task {task_id} completed by {worker_id}")

            # Если есть коллбек для этой задачи - вызываем
            if hasattr(self, f"_callback_{task_id}"):
                callback = getattr(self, f"_callback_{task_id}")
                callback(self.task_results[task_id])
                delattr(self, f"_callback_{task_id}")

        return {"type": MessageType.STATUS.value, "data": {"status": "result_received"}}

    def submit_task(self, task_type: str, task_data: Dict, callback=None) -> str:
        """Добавление задачи в очередь"""
        import uuid
        task_id = str(uuid.uuid4())

        task = {
            "task_id": task_id,
            "type": task_type,
            "data": task_data,
            "priority": task_data.get("priority", 1)
        }

        self.task_queue.append(task)

        # Сохраняем коллбек если он есть
        if callback:
            setattr(self, f"_callback_{task_id}", callback)

        print(f"Task submitted: {task_id} ({task_type})")
        return task_id

    def _dispatch_tasks(self):
        """Диспетчер задач - распределяет задачи по воркерам"""
        import time

        while self.running:
            if self.task_queue:
                task = self.task_queue.popleft()
                task_type = task["type"]

                # Ищем свободного воркера нужного типа
                worker_id = self._find_available_worker(task_type)

                if worker_id:
                    # Отправляем задачу воркеру
                    worker_info = self.workers[worker_id]

                    message = {
                        "type": MessageType.TASK.value,
                        "data": task
                    }

                    response = self.send_message(
                        worker_info["host"],
                        worker_info["port"],
                        message
                    )

                    if response:
                        self.pending_tasks[task["task_id"]] = worker_id
                        print(f"Task {task['task_id']} assigned to {worker_id}")
                    else:
                        # Возвращаем задачу в очередь
                        self.task_queue.appendleft(task)
                else:
                    # Нет свободных воркеров - ждем
                    self.task_queue.appendleft(task)
                    time.sleep(1)
            else:
                time.sleep(0.1)

    def _find_available_worker(self, worker_type: str) -> Optional[str]:
        """Поиск свободного воркера указанного типа"""
        if worker_type not in self.worker_types:
            return None

        for worker_id in self.worker_types[worker_type]:
            if worker_id not in self.pending_tasks.values():
                return worker_id

        return None

    def get_workers_status(self) -> Dict:
        """Получение статуса всех воркеров"""
        status = {}
        for worker_id, info in self.workers.items():
            is_busy = worker_id in self.pending_tasks.values()
            status[worker_id] = {
                "type": info["type"],
                "host": info["host"],
                "port": info["port"],
                "busy": is_busy
            }
        return status
# steam_analysis/app/DistributionEntities/database_worker.py
from .base_worker import BaseWorker
from typing import Dict
import sys
import os


class DatabaseWorker(BaseWorker):
    """Базовый класс для воркеров базы данных"""

    def __init__(self, node_id: str, master_host: str, master_port: int,
                 host: str = "0.0.0.0", port: int = 5002):
        super().__init__(node_id, master_host, master_port, host, port)
        self.db_facade = None

    def _init_db_facade(self, facade_class):
        """Инициализация фасада базы данных"""
        try:
            self.db_facade = facade_class()
            print(f"Database facade initialized for worker {self.node_id}")
        except Exception as e:
            print(f"Error initializing database facade: {e}")
            self.db_facade = None
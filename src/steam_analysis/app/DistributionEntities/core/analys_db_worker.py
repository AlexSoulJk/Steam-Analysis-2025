from typing import Dict

from steam_analysis.app.DistributionEntities.core.base_data_base_worker import DatabaseWorker


class AnalysisDbWorker(DatabaseWorker):
    """Воркер для базы анализа"""

    def __init__(self, node_id: str, master_host: str, master_port: int,
                 host: str = "0.0.0.0", port: int = 5003):
        super().__init__(node_id, master_host, master_port, host, port)

        try:
            from steam_analysis.database.analysis_facade import AnalysisDbFacade
            self._init_db_facade(AnalysisDbFacade)
        except ImportError:
            pass

    def process_task(self, task_data: Dict) -> Dict:
        """Обработка задач базы анализа"""
        if not self.db_facade:
            raise RuntimeError("Analysis DB facade not initialized")

        task_type = task_data.get("task_type")
        data = task_data.get("data", {})

        try:
            if task_type == "get_next_pending_chunk":
                result = self.db_facade.get_next_pending_chunk_by_service(data.get("processor_name"))
                return {"result": result}

            elif task_type == "mark_game_chunk_complete":
                self.db_facade.mark_game_chunk_complete(data)
                return {"status": "success"}

            elif task_type == "get_users_count":
                result = self.db_facade.get_users_count()
                return {"count": result}

            # ... другие методы AnalysisDbFacade

        except Exception as e:
            print(f"Error in AnalysisDbWorker {self.node_id}: {e}")
            raise
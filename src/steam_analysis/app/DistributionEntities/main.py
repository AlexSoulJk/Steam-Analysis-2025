# run_steam_worker.py
import sys
from steam_analysis.app.DistributionEntities.core.worker import SteamAnalysisWorker

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python run_steam_worker.py <worker_id> <master_host> <master_port> <steam_api_key>")
        sys.exit(1)

    worker_id = sys.argv[1]
    master_host = sys.argv[2]
    master_port = int(sys.argv[3])
    api_key = sys.argv[4]

    worker = SteamAnalysisWorker(
        node_id=worker_id,
        master_host=master_host,
        master_port=master_port,
        steam_api_key=api_key,
        host="0.0.0.0",  # Слушаем на всех интерфейсах
        port=0  # 0 - случайный свободный порт
    )

    worker.start()

    print(f"Steam worker {worker_id} started")
    print(f"Connected to master at {master_host}:{master_port}")
    print("Press Ctrl+C to stop")

    try:
        # Бесконечный цикл
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down worker...")
        worker.stop()
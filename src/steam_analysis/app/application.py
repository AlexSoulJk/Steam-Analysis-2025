from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from steam_analysis.database.facade import DbFacade
from steam_analysis.database.analysis_facade import AnalysisDbFacade  # 👈 добавляем
from pathlib import Path
import time


class AppMediator:
    def __init__(self, steam_api_key: str, operator_name: str = "system"):
        self.steam_facade = SteamAnalysisFacade(steam_api_key)
        self.database_facade = DbFacade()
        self.analysis_facade = AnalysisDbFacade()
        self.operator_name = operator_name

    def create_game(self, chunk_size: int = 10):
        # --- Получаем чанк ---
        next_chunk = self.analysis_facade.get_next_chunk()
        if not next_chunk:
            print("❌ Нет чанков для обработки.")
            return

        print(f"⚙️ Обрабатываем чанк {next_chunk.id} "
              f"[{next_chunk.start_app_id}-{next_chunk.end_app_id}]")

        # --- Запрашиваем игры из Steam API ---
        start_time = time.time()
        fill_butch = None
        try:
            fill_butch = self.steam_facade.get_game_analysis_list(
                next_chunk.start_app_id,
                chunk_size
            )
        except Exception as e:
            self.analysis_facade.mark_chunk_failed(next_chunk.id, str(e))
            print(f"❌ Ошибка при загрузке чанка: {e}")
            return
        total_response_time = time.time() - start_time

        # --- Обработка игр и запись в обе базы ---
        processed = 0
        failed = 0
        for game_data in fill_butch.data_chunk:
            if game_data is None:
                failed += 1
                continue

            app_id = game_data.game.appid
            try:
                self.analysis_facade.log_game_analysis(
                    chunk_id=next_chunk.id,
                    app_id=app_id,
                    status="success",
                    response_time=total_response_time / chunk_size,
                    genres=[g.description for g in game_data.genres],
                    categories=[c.description for c in game_data.categories],
                    platforms=[p.description for p in game_data.platforms],
                    stats=None,
                    achievements=None
                )
                processed += 1
            except Exception as e:
                self.analysis_facade.log_game_analysis(
                    chunk_id=next_chunk.id,
                    app_id=app_id,
                    status="failed",
                    error_log=str(e)
                )
                failed += 1

        # --- Сохраняем игры в основную базу ---
        if fill_butch:
            self.database_facade.create_games(fill_butch)

        # --- Завершаем чанк ---
        self.analysis_facade.mark_chunk_completed(
            chunk_id=next_chunk.id,
            null_count=failed,
            not_null_count=processed,
            failed_count=failed
        )

        print(f"✅ Чанк {next_chunk.id} завершён: {processed} успешно, {failed} с ошибками.")

# class AppMediator:
#
#     def __init__(self, steam_api_key: str):
#         self.steam_facade = SteamAnalysisFacade(steam_api_key)
#         self.database_facade = DbFacade()
#
#     def create_game(self, chunk_size: int = 10):
#         # Main game filling case
#         game = self.database_facade.get_last_upploaded_game()
#         start_app_id = self.steam_facade.get_first_app_id() if game is None else game.app_id
#         fill_butch = self.steam_facade.get_game_analysis_list(start_app_id, chunk_size)
#         # fill_butch = default_loader.load_fill_game_batch(Path("games_30_130_20251006.json"))
#         # default_saver.save_fill_game_batch(fill_butch)
#         print("fill_butch: ", fill_butch)
#         self.database_facade.create_games(fill_butch)
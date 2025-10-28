from steam_analysis.database.analysis_facade import AnalysisDbFacade

PROCESSOR_NAME = ["AlexSoulJK",
                  "baru1ina",
                  "Ekaterina Lips",
                  "Lo-Lap"]


def main():
    adbfacade = AnalysisDbFacade()
    chunk = adbfacade.get_next_pending_chunk_by_service(PROCESSOR_NAME[0])
    # Дополнительных запросов НЕТ
    for game in chunk.games:
        print(game.status)
    # print(chunk.games)


if __name__ == "__main__":
    main()

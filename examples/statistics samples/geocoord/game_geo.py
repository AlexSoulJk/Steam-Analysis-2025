import datetime

from steam_analysis.proccessors.geo_game_proccesor import GeoProccessor

tmp = datetime.datetime.now()
gp = GeoProccessor()
print(gp.get_games_by_geo())
elapsed = (datetime.datetime.now() - tmp).seconds
print(elapsed)

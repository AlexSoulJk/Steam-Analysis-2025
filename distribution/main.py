
# .exe --fill_strategy -g path_config
# .exe --create_users_strategy

# .exe --create_games
# .exe --add_schema

# .exe -- create_strategy -g config_path
# .exe update_strategy -g config_path

# .exe --collect_data config_path

# Содержит точна:
# Сущность: str =  [Player, Game]
# Номер stage: int = [0,1]
# Имя процессора: str = "FullSuccesser"

# .exe --fill_analys_db config_path

# Содержит точна:
# Сущность: subject: str =  [Player, Game]
# Номер stage: int = [0,1]

# .exe --calculate config_path
# Содержит точна:
# Номер таски: task: Union[List[int], str] = [0 ... 4] (по умолчанию "all")
# Номер графика: graph Union[List[int], str] [0, 1 ..]  = (по умолчанию "all")

# .exe --google_load config_path
# Содержит точна:
# Номер таски: task: Union[List[int], str]  =  [0 ... 4] (по умолчанию "all")
# Номер графика: graph: Union[List[int], str]=  [0, 1 ..] (по умолчанию "all")

# .exe --visualize config_path
# Содержит точна:
# Номер таски: task: Union[List[int], str] =  [0 ... 4] (по умолчанию "all")
# Номер графика: Union[List[int], str] = graph [0, 1 ..] (по умолчанию "all")

def main():

    # args = аргументы
    # args -> те что нам нужны fill_strategy()


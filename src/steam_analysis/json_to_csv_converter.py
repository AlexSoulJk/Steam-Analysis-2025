import csv
import io

import pandas as pd

from steam_analysis.core.schemas.analysis.friends import FriendsByGames
from steam_analysis.core.schemas.analysis.geoshemas import ListCountryGameStat, CountryGameStat


class JsonToCsvConverter:

    def __init__(self):
        pass

    def convert_geo_games(self, obj: ListCountryGameStat) -> str:
        """
        Конвертирует ListCountryGameStat в CSV строку

        Args:
            obj: объект ListCountryGameStat с данными

        Returns:
            CSV строка с данными
        """
        if not obj.data:
            return ""

        # Создаем строковый буфер для CSV
        output = io.StringIO()

        # Определяем заголовки из полей модели
        headers = list(CountryGameStat.__annotations__.keys())

        # Создаем writer
        writer = csv.DictWriter(output, fieldnames=headers)

        # Записываем заголовки
        writer.writeheader()

        # Записываем данные
        for item in obj.data:
            writer.writerow(item.model_dump())

        # Получаем CSV строку
        csv_string = output.getvalue()
        output.close()

        return csv_string

    def convert_for_cosmograph(self, data: FriendsByGames):
        # --- 1. Обработка УЗЛОВ (Nodes) ---

        # ИСПРАВЛЕНИЕ: Превращаем Pydantic модели в список словарей
        # Если у вас Pydantic v2:
        nodes_data = [node.model_dump() for node in data.nodes]
        # Если Pydantic v1 (старый), используйте: [node.dict() for node in data.nodes]

        df_nodes = pd.DataFrame(nodes_data)

        # Теперь колонки будут называться нормально ('id', 'name'...), а не 0, 1, 2

        # Логика с count
        if 'count' in df_nodes.columns:
            df_nodes['count'] = df_nodes['count'].fillna(1).astype(int)
        else:
            df_nodes['count'] = 0

        print(f"Nodes prepared: {len(df_nodes)} rows")

        # --- 2. Обработка СВЯЗЕЙ (Orts/Edges) ---

        # ИСПРАВЛЕНИЕ: То же самое для связей
        # Pydantic v2:
        orts_data = [ort.model_dump() for ort in data.orts]
        # Pydantic v1: [ort.dict() for ort in data.orts]

        df_orts = pd.DataFrame(orts_data)

        # Если нужно переименовать для Cosmograph (обычно он хочет source/target)
        # df_orts = df_orts.rename(columns={'from': 'source', 'to': 'target'})

        return df_nodes, df_orts

    def convert_for_cosmograph(self, data: FriendsByGames):

        # --- 1. Распаковка данных ---
        nodes = [n.model_dump() for n in data.nodes]
        orts = [o.model_dump() for o in data.orts]

        df_nodes = pd.DataFrame(nodes)
        df_orts = pd.DataFrame(orts)

        # --- 2. Подготовка словарей ---
        id_to_name = df_nodes.set_index('id')['name'].to_dict()
        id_to_type = df_nodes.set_index('id')['type'].to_dict()

        # Пытаемся достать ссылку на профиль, иначе генерируем поиск
        if 'url' in df_nodes.columns:
            id_to_url = df_nodes.set_index('id')['url'].to_dict()
        else:
            id_to_url = {i: f"https://steamcommunity.com/search/users/#text={n}" for i, n in
                         zip(df_nodes['id'], df_nodes['name'])}

        # Находим ID Таргета (Тебя)
        try:
            target_node_id = df_nodes[df_nodes['type'] == 'target']['id'].iloc[0]
        except IndexError:
            target_node_id = None  # На случай, если таргета нет в нодах

        # --- 3. Сбор статистики: Кто играет в игру? ---
        game_friends_map = {}

        for _, row in df_orts.iterrows():
            source_id = row['source']  # Кто
            target_id = row['target']  # Во что

            source_type = id_to_type.get(source_id)
            target_type = id_to_type.get(target_id)

            # Собираем инфу только если Друг -> Игра
            if source_type == 'friend' and target_type == 'game':
                friend_name = id_to_name.get(source_id, "Unknown")
                friend_url = id_to_url.get(source_id, "")

                if target_id not in game_friends_map:
                    game_friends_map[target_id] = []

                game_friends_map[target_id].append((friend_name, friend_url))

        # --- 4. Формируем УЗЛЫ (Игры + Таргет) ---
        final_nodes = df_nodes[df_nodes['type'].isin(['game', 'target'])].copy()

        def generate_pretty_description(row):
            # А. Если это ТЫ
            if row['type'] == 'target':
                return "### Это твой профиль"

            # Б. Если это ИГРА
            game_id_raw = row['id']

            # Ссылка на магазин
            try:
                app_id = row['app_id']
                store_url = f"https://store.steampowered.com/app/{app_id}/"
            except:
                store_url = "#"

            # Заголовок
            desc_parts = [f"### [{row['name']}]({store_url})"]

            # Список друзей
            friends_data = game_friends_map.get(game_id_raw, [])

            if friends_data:
                # Сортируем по имени, чтобы было аккуратно
                friends_data.sort(key=lambda x: x[0].lower())

                desc_parts.append(f"**Друзей: {len(friends_data)}**")
                desc_parts.append("---")  # Линия

                # Формируем компактный список
                for name, url in friends_data:
                    link = f"[{name}]({url})" if url else name
                    desc_parts.append(f"* {link}")
            else:
                desc_parts.append("\n_Друзья пока не играют_")

            return "\n\n".join(desc_parts)

        # Генерируем картинки
        def get_steam_image(row):
            if row['type'] == 'game':
                try:
                    app_id = row['app_id']
                    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                except:
                    return ""
            elif row['type'] == 'target':
                # Если есть аватарка в данных - вставь сюда row['avatar']
                return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/2048px-Steam_icon_logo.svg.png"
            return ""

        final_nodes['Description'] = final_nodes.apply(generate_pretty_description, axis=1)
        final_nodes['Image'] = final_nodes.apply(get_steam_image, axis=1)

        # Переименовываем для Kumu
        final_nodes = final_nodes.rename(columns={
            'name': 'Label', 'type': 'Type', 'id': 'ID', 'count': 'HoursPlayed'
        })

        # Финальная таблица узлов
        final_nodes = final_nodes[['ID', 'Label', 'Type', 'Description', 'HoursPlayed', 'Image']]

        # --- 5. Формируем СВЯЗИ (Connections) ---
        # ИСПРАВЛЕНИЕ: Берем только реальные связи из данных

        connections = []

        if target_node_id:
            for _, row in df_orts.iterrows():
                source_id = row['source']
                target_id = row['target']

                # Проверяем: Связь должна идти ОТ ТЕБЯ (Target) -> К ИГРЕ (Game)
                # Мы игнорируем связи Friend->Game для отрисовки линий,
                # так как друзей нет на карте как узлов.
                if source_id == target_node_id:
                    # Проверяем, что цель действительно игра (на всякий случай)
                    if id_to_type.get(target_id) == 'game':
                        connections.append({
                            'From': source_id,
                            'To': target_id,
                            'Type': 'owns'  # Или 'plays'
                        })

        df_connections = pd.DataFrame(connections)

        return final_nodes, df_connections


classDiagram
direction BT
class alembic_version {
   varchar(32) version_num
}
class categories {
   varchar(100) name
   varchar(255) description
   datetime created_at
   datetime updated_at
   integer id
}
class game_categories {
   integer game_id
   integer category_id
   datetime created_at
   datetime updated_at
   integer id
}
class game_genres {
   integer game_id
   integer genre_id
   datetime created_at
   datetime updated_at
   integer id
}
class game_metrics {
   integer game_id
   integer recommendations_count
   integer metacritic_score
   float review_score
   integer review_count
   integer peak_players_all_time
   datetime last_updated
   datetime created_at
   datetime updated_at
   integer id
}
class game_platforms {
   integer game_id
   integer platform_id
   boolean supported
   datetime created_at
   datetime updated_at
   integer id
}
class game_types {
   varchar(100) name
   varchar(255) description
   datetime created_at
   datetime updated_at
   integer id
}
class games {
   integer app_id
   varchar(255) name
   integer type_id
   boolean is_free
   datetime release_date
   boolean coming_soon
   varchar(50) controller_support
   datetime created_at
   datetime updated_at
   integer id
}
class genres {
   varchar(100) name
   varchar(255) description
   datetime created_at
   datetime updated_at
   integer id
}
class platforms {
   varchar(100) name
   varchar(255) description
   datetime created_at
   datetime updated_at
   integer id
}
class player_count_history {
   integer game_id
   integer player_count
   datetime recorded_at
   datetime created_at
   datetime updated_at
   integer id
}
class price_history {
   integer game_id
   varchar(3) currency
   integer price_final
   integer discount_percent
   datetime recorded_at
   datetime created_at
   datetime updated_at
   integer id
}
class sqlite_master {
   text type
   text name
   text tbl_name
   int rootpage
   text sql
}

game_categories  -->  categories : category_id:id
game_categories  -->  games : game_id:id
game_genres  -->  games : game_id:id
game_genres  -->  genres : genre_id:id
game_metrics  -->  games : game_id:id
game_platforms  -->  games : game_id:id
game_platforms  -->  platforms : platform_id:id
games  -->  game_types : type_id:id
player_count_history  -->  games : game_id:id
price_history  -->  games : game_id:id

| Название модели    | Название схемки    | Поля    | 
|---|---|---|
|game.Stats     |base.StatsMixin    |name: str<br>default_value: int <br>display_name: str    |
|-     |base.GlobalStatsMixin    |    |
|game.Achievement     |base.AchievMixin    |name: str<br>default_value: int <br>display_name: str<br>hidden: <br>icon: str<br>icon_gray: str    |
|timeseries.AchievementHistory     |base.AchievPercentMixin    |achievement_name: str<br>percent: float    |
|player.User     |base.ReviewAuthorMixin    |steam_id: str<br>num_games_owned: int<br>num_reviews: int<br>playtime_forever: int<br>playtime_last_two_weeks: int<br>playtime_at_review: int<br>last_played: int    |
|playergame.Review     |base.ReviewMixin    |recommendation_id: str<br>author: ReviewAuthorMixin<br>language: str<br>review: str<br>timestamp_created: int<br>timestamp_updated: int<br>voted_up: bool<br>votes_up: int<br>votes_funny: int<br>weighted_vote_score: float<br>comment_count: int<br>steam_purchase: bool<br>received_for_free: bool<br>written_during_early_access: bool<br>primarily_steam_deck: bool    |
|timeseries.ReviewHistory     |service.ReviewsDataAnalysisCreate    |    game_id: int<br>num_reviews: int<br>review_score: int<br>review_score_desc: str<br>total_positive: int<br>total_negative: int<br>total_reviews: int    |
|game.News     |base.NewMixin    |gid: str<br>title: str<br>url: str<br>is_external_url: bool<br>author: str<br>contents: str<br>feedlabel: str<br>date: int<br>feedname: str<br>feed_type: int    |

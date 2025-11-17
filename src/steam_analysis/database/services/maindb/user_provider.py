from sqlalchemy.orm import Session

from steam_analysis.database.repositories import UserRepository


class UserProviderService:

    def __init__(self):
        self.game_repos = UserRepository()
        pass

    def get_last_upploaded_game(self, session: Session):
        return self.game_repos.get_last_uploaded_game(session=session)

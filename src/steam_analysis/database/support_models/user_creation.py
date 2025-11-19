from dataclasses import dataclass
from typing import Dict

from steam_analysis.database.models import Review
from steam_analysis.database.models.game import Achievement
from steam_analysis.database.models.player import *


@dataclass
class PreparedForUserCreation:
    achievements: Dict[str, Achievement]
    reviews: Dict[str, Review]

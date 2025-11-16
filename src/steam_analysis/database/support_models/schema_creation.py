from dataclasses import dataclass
from typing import Dict

from steam_analysis.database.models.game import Achievement, Statistic


@dataclass
class PreparedForSchemaCreation:
    achievs: Dict[str, Achievement]
    # stats: Dict[str, Statistic]


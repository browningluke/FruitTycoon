# Internal Python Moduels
import os
import logging

from .json import Json

log = logging.getLogger("root")
log.debug("playerIndex.py loaded")

class PlayerIndex:

    file_location = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/index.json"

    def __init__(self):
        self.list = self.load()

    # I/O
    # ---------------------------
    def load(self):
        """Load index from json"""
        players = Json(PlayerIndex.file_location).get("players", fallback=[])
        return players

    def save(self):
        """Save index to json"""
        Json(PlayerIndex.file_location, load=False).dump({"players": self.list})

    # Players
    # ---------------------------
    async def add(self, player_id):
        self.list.append(player_id)
        self.save()

    async def remove(self, player_id):
        self.list.remove(player_id)
        self.save()

    async def exists(self, player_id):
        for x in self.list:
            if x == player_id:
                return True
        else:
            return False


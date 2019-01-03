# Internal Python Modules
import os
import logging

# Imported (External) Python Modules
import discord
from .discordClient import DiscordClient

# Game
from .playerIndex import PlayerIndex
from .player import Player
from .trade import Trade

# Misc
from .json import Json

log = logging.getLogger("root")
log.debug("game.py loaded")

class GameManager:

    config_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/config/config.json"

    def __init__(self):
        self.config = self.load_config()
        
        self.players = PlayerIndex()
        self.client = DiscordClient(self)
        

    # Config
    # ---------------------------

    def load_config(self):
        """Loads config from file."""
        conf = Json(GameManager.config_path).data
        return conf

    # Players
    # ---------------------------

    # Player I/O

    async def get_player(self, player_id):
        pass

    # Game
    # ---------------------------

    async def join_game(self):
        pass

    async def harvest_fruit(self):
        pass

    async def get_profile(self):
        pass

    async def get_leaderboard(self):
        pass

    async def upgrade_stat(self):
        pass

    # Admin
    # ---------------------------

    async def reset_game(self):
        pass

    async def get_player_profile(self):
        pass

    # Misc
    # ---------------------------

    def start_game(self):
        # Start game stuff
        self.client.start_bot(self.config["credentials"]["token"])

if __name__ == "__main__":
    GameManager().start_game()
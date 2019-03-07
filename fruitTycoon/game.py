# Internal Python Modules
import os
import asyncio
import logging
import time
import copy
from datetime import datetime, time

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
    data_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/game_data.json"

    def __init__(self):
        self.config = self.load_config()
        self.game_data = Json(GameManager.data_path).data
        
        self.players = PlayerIndex()
        self.client = DiscordClient("a.", self.game_data, game=self)
        

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
        if await self.players.exists(player_id):
            player = Player(player_id)
            player.load()
            return player
        return None

    async def remove_player(self, player_id):
        await self.players.remove(player_id)
        player = Player(player_id)
        player.delete()

        return True

    # Game
    # ---------------------------

    async def join_game(self, ctx, fruit_type):
        player = Player(ctx.message.author.id, fruit_type.lower())
        player.last_harvest = int(time.time())
        
        await self.players.add(player.id)
        player.save()

        return True
        
    async def harvest(self, player_id):
        player = Player(player_id)
        player.load()

        # Ensure sufficient time has passed (2 hours = 7200 seconds)
        if int(time.time()) - player.last_harvest < 7200:
            return {
                "time_valid": False,
                "time_remaining": 7200 - (int(time.time()) - player.last_harvest)
            }

        # Calculate harvest yield
        harvest_yield = 1000 + (1500 * (player.upgrades["size"]-1))
        harvest_yield *= player.upgrades["multiplier"]

        # Add harvest yield to player's inventory
        if player.type == "apple": player.inventory["apple"] += harvest_yield
        if player.type == "banana": player.inventory["banana"] += harvest_yield
        if player.type == "grape": player.inventory["grape"] += harvest_yield

        player.last_harvest = int(time.time()) # Update last harvest
        player.save()
        
        return {
            "time_valid": True,
            "harvest_yield": harvest_yield,
            "type": player.type
        }
        
    async def get_profile(self, member, embed):
        player = Player(member.id)
        player.load()

        # Format profile
        profile_embed = copy.deepcopy(embed)
        profile_embed["title"] = profile_embed["title"].format(member.name)
        profile_embed["fields"][0]["value"] = profile_embed["fields"][0]["value"].format(
            "grapes" if player.type == "grape" else player.type
        ) # Type
        profile_embed["fields"][1]["value"] = profile_embed["fields"][1]["value"].format(player.money) # Money
        
        # Time of last harvest
        time_since_lh = int(time.time()) - player.last_harvest
        hours, minutes = divmod((time_since_lh // 60), 60) # Convert seconds to minutes, then calculate hours & minutes
        profile_embed["fields"][2]["value"] = profile_embed["fields"][2]["value"].format(
            str(hours) + " hours " + str(minutes) + " minutes"
        )

        # Inventory
        profile_embed["fields"][3]["value"] = profile_embed["fields"][3]["value"].format(
            player.inventory["apple"], player.inventory["banana"], player.inventory["grape"]
        )

        # Trades
        # TODO: Add trade formating once trade system implemented

        # Farm Stats
        profile_embed["fields"][6]["value"] = profile_embed["fields"][6]["value"].format(
            player.upgrades["size"], player.harvest_amount
        )
        profile_embed["fields"][7]["value"] = profile_embed["fields"][7]["value"].format(player.upgrades["multiplier"])

        return profile_embed

    async def get_leaderboard(self):
        pass

    async def upgrade_stat(self):
        pass

    async def leaderboard_day_loop(self):
        while True:
            target = datetime.combine(datetime.today(), time.max)
            current_time = datetime.now()
            delta = int((target - current_time).total_seconds())

            print("leaderboard")
            log.debug("sleeping for {} seconds".format(delta))

            await asyncio.sleep(delta)

    # Admin
    # ---------------------------

    async def reset_game(self):
        pass

    # Misc
    # ---------------------------

    def start_game(self):
        # Start game stuff
        self.client.start_bot(self.config["credentials"]["token"])

if __name__ == "__main__":
    GameManager().start_game()
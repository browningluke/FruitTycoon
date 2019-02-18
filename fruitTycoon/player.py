import os
import logging

from .trade import Trade
from .json import Json

log = logging.getLogger("root")
log.debug("player.py loaded")

class Player:

    player_file = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/player_data/"

    def __init__(self, player_id, f_type=None):
        self.id = player_id
        
        # Profile variables
        self.type = f_type
        self.money = 0
        self.last_harvest = 0
        self.inventory = {
            "apple": 0,
            "banana": 0,
            "grape": 0
        }

        # Trades
        self.in_trade = [0] * 6
        self.out_trade = [0] * 6

        self.upgrades = {
            "size": 1,
            "multiplier": 1
        }

        self.harvest_amount = 0
        self.planting_cost = 0
        
        self.max_harvest_percent = 0
        self.max_harvest_percent = 0

    async def send_trade(self, player):
        trade = Trade(self, player)

        self.out_trade.append(trade)
        player.in_trade.append(trade)

        # trade

    async def generate_profile(self, raw_embed):
        embed = raw_embed
        return embed

    def save(self):
        """Save player variables to JSON."""

        # Get object variables as string
        json_string = self.__dict__

        log.info(json_string)

        # Dump the string to JSON
        succeeded = Json(Player.player_file + "{}.json".format(self.id), load=False).dump(json_string)

        if succeeded:
            return True
        else:
            log.warning("Could not save player")
            return None

    def load(self):
        """Load player variables from JSON."""

        # Load json string from JSON
        json_string = Json(Player.player_file + "{}.json".format(self.id)).data

        # Set instance variables to loaded variables
        try:
            self.__dict__ = json_string
        except Exception as e:
            log.error(e)
            return None

        return True

    def delete(self):
        """Delete player variables from JSON."""
        try:
            os.remove(Player.player_file + "{}.json".format(self.id))
        except Exception as e:
            log.error(e)
            return None
        return True
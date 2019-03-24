import os
import time
import logging
from discord import Embed

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
        self.in_trade = [0] * 4
        self.out_trade = [0] * 4

        self.upgrades = {
            "size": 1000,
            "multiplier": 1,
            "farm": []
        }
        self.upgrade_levels = {
            "size": 1,
            "multiplier": 1
        }

        self.farm_level = 0 # Determines if the user can produce stuff

        self.planting_cost = 0
        
        self.max_harvest_percent = 0
        self.max_harvest_percent = 0

    def create_profile_embed(self, template, name, avatar_url):
        """Creates a discord.Embed from the template "join" in the game_data.json file.
        
        Arguments:
            template {dict} -- Contains the template for the embed file.
        
        Returns:
            discord.Embed -- A discord.Embed object containing the details of the trade.
        """
        
        embed = template[0]

        embed["title"] = embed["title"].format(name)
        embed["thumbnail"]["url"] = embed["thumbnail"]["url"].format(avatar_url)
        
        # Type
        embed["fields"][0]["value"] = embed["fields"][0]["value"].format(
            "grapes" if self.type == "grape" else self.type
        ) 

        # Time of last harvest
        time_since_lh = int(time.time()) - self.last_harvest
        hours, minutes = divmod((time_since_lh // 60), 60) # Convert seconds to minutes, then calculate hours & minutes
        embed["fields"][1]["value"] = embed["fields"][1]["value"].format(
            str(hours) + " hours " + str(minutes) + " minutes"
        )

        # Inventory
        embed["fields"][2]["value"] = embed["fields"][2]["value"].format(
            self.inventory["apple"], self.inventory["banana"], self.inventory["grape"]
        )

        # Money
        embed["fields"][3]["value"] = embed["fields"][3]["value"].format(self.money)

        # Trades
        trade_embed = self._create_trade_embed(template[1])

        # Farm Stats
        embed["fields"][4]["value"] = embed["fields"][4]["value"].format(
            self.upgrade_levels["size"], self.upgrades["size"]
        )
        embed["fields"][5]["value"] = embed["fields"][5]["value"].format(self.upgrades["multiplier"])
        
        # Purchased Upgrades
        if not self.upgrades["farm"] == []:
            farm_upgrades = "\n".join(self.upgrades["farm"])
        else:
            farm_upgrades = "None"
        embed["fields"][6]["value"] = embed["fields"][6]["value"].format(farm_upgrades)

        return Embed().from_data(embed), trade_embed

    def _create_trade_embed(self, template):
        embed = template
        
        def convert_short_text(short_text):
            if short_text == "money":
                return "moneybag"
            elif short_text == "grape":
                return "grapes"
            else:
                return short_text
        
        in_trade = []
        for x in self.in_trade:
            if x == 0:
                in_trade.append("")
            else:
                string = "{}: {}x{} for {}x{}.".format(
                    x.sender_name,
                    ":{}:".format(convert_short_text(x.request[0])), x.request[1],
                    ":{}:".format(convert_short_text(x.offer[0])), x.offer[1],
                )
                in_trade.append(string)
        
        out_trade = []
        for x in self.out_trade:
            if x == 0:
                out_trade.append("")
            else:            
                string = "{}: {}x{} for {}x{}.".format(
                    x["recipient_name"],
                    ":{}:".format(convert_short_text(x["request"][0])), x["request"][1],
                    ":{}:".format(convert_short_text(x["offer"][0])), x["offer"][1]
                )
                out_trade.append(string)
        
        embed["fields"][0]["value"] = embed["fields"][0]["value"].format(*in_trade)
        embed["fields"][1]["value"] = embed["fields"][1]["value"].format(*out_trade)

        return Embed().from_data(embed)

    def create_join_embed(self, template, name):
        """Creates a discord.Embed from the template "join" in the game_data.json file.
        
        Arguments:
            template {dict} -- Contains the template for the embed file.
        
        Returns:
            discord.Embed -- A discord.Embed object containing the details of the trade.
        """
        embed = template

        embed["title"] = embed["title"].format(name)
        embed["description"] = embed["description"].format(name)

        return Embed().from_data(embed)

    def create_shop_embed(self, template, member, prefix, juice_upgrades):
        embed = template
        
        # Create shop embed
        embed["description"] = embed["description"].format(member.name)
        
        # Farm Size
        embed["fields"][0]["value"] = embed["fields"][0]["value"].format(
            self.upgrade_levels["size"]+1, self.calculate_upgrade("size")
        )
        
        # Multiplier
        embed["fields"][1]["value"] = embed["fields"][1]["value"].format(
            self.calculate_upgrade("multiplier", price=False), 
            self.calculate_upgrade("multiplier")
        )
        
        # Farm Utilities (Juice type)
        if not self.farm_level == 4:
            embed["fields"][2]["value"] = embed["fields"][2]["value"].format(
                juice_upgrades[juice_upgrades["id_to_name"][str(self.farm_level+1)]]["name"], 
                juice_upgrades[juice_upgrades["id_to_name"][str(self.farm_level+1)]]["unlock_price"], 
                juice_upgrades[juice_upgrades["id_to_name"][str(self.farm_level+1)]]["description"]
            )
        else:
            embed["fields"][2]["value"] = embed["fields"][2]["value"].format("This cannot be upgraded any higher.")

        # Create shop help embed
        embed_help = {
            "description": "To purchase, type `{}upgrade [size/multiplier/farm]`".format(
                prefix
            ),
            "color": 3060770
        }
        
        return Embed().from_data(embed), Embed().from_data(embed_help)

    def calculate_upgrade(self, upgrade, price=True):
        # This is where the formulas are hard-coded in.
        # So change them here.

        upgrade_formula = {
            "size": {
                "price": lambda n: 10000 * (1.25 ** (n-1)),
                "value": lambda n: int(1000 + (1500 * (n-1)))
            },
            "multiplier": {
                "price": lambda n: 1000 * (1.5 ** (n-1)),
                "value": lambda n: 1 + (0.1 * (n-1))
            }}

        if price:
            return int(upgrade_formula[upgrade]["price"](self.upgrade_levels[upgrade]))
        return upgrade_formula[upgrade]["value"](self.upgrade_levels[upgrade]+1)

    def save(self):
        """Save player variables to JSON."""

        # Check for and save Incoming Trades
        if not self.in_trade == [0] * 4:
            for pos, trade in enumerate(self.in_trade):
                if trade == 0:
                    continue
                self.in_trade[pos] = self.in_trade[pos].save_string()

        # Get object variables as string
        json_string = self.__dict__

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

        # Check for and load Incoming Trades
        if not self.in_trade == [0] * 4:
            for pos, trade_string in enumerate(self.in_trade):
                if trade_string == 0:
                    continue
                trade = Trade()
                trade.load_string(trade_string)
                self.in_trade[pos] = trade

        return True

    def delete(self):
        """Delete player variables from JSON."""
        try:
            os.remove(Player.player_file + "{}.json".format(self.id))
        except Exception as e:
            log.error(e)
            return None
        return True
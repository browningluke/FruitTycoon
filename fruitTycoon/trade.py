import copy
import logging
from discord import Embed

log = logging.getLogger("root")
log.debug("trade.py loaded")

class Trade:

    def __init__(self, sender=None, recipient=None, request=None, offer=None):
        """Holds the details of the trade, and stored in recipient's inbox.
        
        Keyword Arguments:
            sender {tuple} -- (discord.Member, name, slot) (default: {None})
            recipient {tuple} -- (discord.Member, name, slot) (default: {None})
            request {tuple} -- (fruit_type, quantity) (default: {None})
            offer {tuple} -- (fruit_type, quantity) (default: {None})
        """

        if sender is not None and recipient is not None:
            self.sender = sender[0] # Created as discord.Member, becomes id after save/load
            self.recipient = recipient[0] # Created as discord.Member, becomes id after save/load

            self.sender_name = sender[1]
            self.recipient_name = recipient[1]

            self.sender_slot = sender[2]
            self.recipient_slot = recipient[2]

        self.request = request
        self.offer = offer

    def _convert_short_text(self):
        if self.request[0] == "grape": 
            request = "grapes"
        elif self.request[0] == "money": 
            request = "moneybag"
        else: 
            request = self.request[0]

        if self.offer[0] == "grape": 
            offer = "grapes"
        elif self.offer[0] == "money": 
            offer = "moneybag"
        else: 
            offer = self.offer[0]

        return request, offer

    def create_confirmation_embed(self, template):
        """Creates a discord.Embed from the template "trade_confirmation" in the game_data.json file.
        
        Arguments:
            template {dict} -- Contains the template for the embed file.
        
        Returns:
            discord.Embed -- A discord.Embed object containing the details of the trade.
        """
        embed = copy.deepcopy(template)
        
        embed["title"] = embed["title"].format(self.recipient.name)
        thumbnail = self.recipient.avatar_url if not self.recipient.avatar_url == "" else self.recipient.default_avatar_url
        embed["thumbnail"]["url"] = embed["thumbnail"]["url"].format(thumbnail)
        embed["author"]["name"] = embed["author"]["name"].format(self.sender.name)
        icon = self.sender.avatar_url if not self.sender.avatar_url == "" else self.sender.default_avatar_url
        embed["author"]["icon_url"] = embed["author"]["icon_url"].format(icon)
        
        
        request, offer = self._convert_short_text()
        embed["fields"][0]["value"] = embed["fields"][0]["value"].format(request, self.request[1])
        embed["fields"][1]["value"] = embed["fields"][1]["value"].format(offer, self.offer[1])

        return Embed().from_data(embed)

    def create_incoming_embed(self, template):
        """Creates a discord.Embed from the template "trade_incoming" in the game_data.json file.
        
        Arguments:
            template {dict} -- Contains the template for the embed file.
        
        Returns:
            discord.Embed -- A discord.Embed object containing the details of the trade.
        """
        embed = copy.deepcopy(template)

        embed["description"] = embed["description"].format(self.sender.name)
        thumbnail = self.recipient.avatar_url if not self.recipient.avatar_url == "" else self.recipient.default_avatar_url
        embed["thumbnail"]["url"] = embed["thumbnail"]["url"].format(thumbnail)
        embed["author"]["name"] = embed["author"]["name"].format(self.sender.name)
        icon = self.sender.avatar_url if not self.sender.avatar_url == "" else self.sender.default_avatar_url
        embed["author"]["icon_url"] = embed["author"]["icon_url"].format(icon)


        request, offer = self._convert_short_text()
        embed["fields"][0]["value"] = embed["fields"][0]["value"].format(request, self.request[1])
        embed["fields"][1]["value"] = embed["fields"][1]["value"].format(offer, self.offer[1])

        return Embed().from_data(embed)

    def load_string(self, string):
        """Load Trade variables from string."""

        # Set instance variables to loaded variables
        try:
            self.__dict__ = string
        except Exception as e:
            log.error(e)
            return None

        return True


    def save_string(self):
        """Save Trade variables to string."""
        
        # Sender & Recipient serialize to their id
        if not isinstance(self.sender, str) or not isinstance(self.recipient, str):
            self.sender = self.sender.id
            self.recipient = self.recipient.id
        
        # print(self.__dict__)
        return self.__dict__
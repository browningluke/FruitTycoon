# Internal Python Modules
import os
import asyncio
import logging
import time
import datetime
import copy

# Imported (External) Python Modules
import discord
from .discordClient import DiscordClient

# Game
from .playerIndex import PlayerIndex
from .player import Player
from .trade import Trade
from .logger import setup_discord_logger, set_logger_level

# Misc
from .json import Json

log = logging.getLogger("root")
log.debug("game.py loaded")

class GameManager:

    config_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/config/config.json"
    data_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/game_data.json"
    log_path = ""

    def __init__(self):
        self.config = self.load_config()
        self.game_data = Json(GameManager.data_path).data
        self.players = PlayerIndex()
        self.client = DiscordClient(self.config, self.game_data, game=self)
        
        # Leaderboard
        self.leaderboard_embed = None
        self.leaderboard_channel = self.config["chat"]["leaderboard_channel"]


        # Defined in game_data.json
        self.embeds = self.game_data["embeds"]

        # Setup loggers
        set_logger_level(log, self.config["bot"]["debug_level"])
        if self.config["bot"]["discord_debug_mode"]:
            setup_discord_logger(GameManager.log_path)
        

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

    # Helper functions
    # ---------------------------

    async def is_player(self, member, error_message=None):
        # Ensure the user has already joined
        # TODO: (FUTURE) change into decorator
        if await self.get_player(member.id) is None: 
            message = "You have to join the game to run this command." if error_message is None else error_message
            await self.client.send_message(member, content=message)
            return False
        return True

    def _convert_short_text(self, short_text):
        if short_text == "money":
            return "moneybag"
        elif short_text == "grape":
            return "grapes"
        else:
            return short_text

    def _check_types(self, raw):
        if raw is None: 
            return False
        if raw.lower() in self.game_data["fruits"]: 
            return True
    
    # Game
    # ---------------------------

    async def join_game(self, ctx, fruit_type):
        # Get (discord) member object from context
        member = ctx.message.author 
        
        # Ensure the user had not already joined
        if await self.get_player(member.id) is not None: 
            await self.client.send_message(member, content="You have already joined the game.")
            return

        # Ensure the user has entered a valid fruit type            
        if fruit_type is None:
            # Get fruit type via reaction dialogue
            emojis = {"\U0001F34E": "apple", "\U0001F34C": "banana", "\U0001F347": "grape"}
            
            msg = await self.client.send_message(member, "Choose a fruit type!")
            await self.client.add_reactions(msg, emojis.keys())
            res = await self.client.wait_for_reaction(emoji=list(emojis.keys()), message=msg, user=member)

            fruit_type = emojis[res.reaction.emoji]
            private = True
        
        elif not self._check_types(fruit_type):
            await self.client.send_message(ctx.message.channel, "<@{}> Please enter a valid fruit type. They are:\n- {}".format(member.id, '\n- '.join(self.client.fruit_types)))
            return

        # Create player instance
        player = Player(ctx.message.author.id, fruit_type.lower())
        player.last_harvest = int(time.time())

        # Send user welcome embed
        join_embed = player.create_join_embed(copy.deepcopy(self.embeds["join"]), member.name)

        await self.client.send_typing(ctx.message.channel)
        await self.client.send_message(member, content=None, embed=join_embed)
        
        if not ctx.message.channel.is_private or not private: 
            await self.client.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))
        
        await self.client.send_message(member, 
        "You've chosen :{}:. We'll plant your first lot for you. Run the harvest command in {} hours.".format(self._convert_short_text(fruit_type), "2"))
    
        await self.players.add(player.id)
        player.save()
        
    async def harvest(self, ctx):
        # Get (discord) member object from context
        member = ctx.message.author 

        # Ensure the user has already joined
        if not await self.is_player(member): return
        
        # Load player
        player = await self.get_player(member.id)

        # Ensure sufficient time has passed (2 hours = 7200 seconds)
        time_valid = True
        if int(time.time()) - player.last_harvest < 7200:
            time_valid = False
            time_remaining = 7200 - (int(time.time()) - player.last_harvest)

        # Calculate harvest yield
        harvest_yield = player.upgrades["size"]
        harvest_yield *= player.upgrades["multiplier"]
        harvest_yield = int(harvest_yield)

        # Add harvest yield to player's inventory
        if player.type == "apple": 
            player.inventory["apple"] += harvest_yield
        if player.type == "banana": 
            player.inventory["banana"] += harvest_yield
        if player.type == "grape": 
            player.inventory["grape"] += harvest_yield

        player.last_harvest = int(time.time()) # Update last harvest
        player.save()
        
        # Send message
        if not time_valid:
            hours, minutes = divmod((time_remaining // 60), 60) # Convert seconds to minutes, then calculate hours & minutes
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "<@{}>, your fruit has not fully grown. ({} hour(s) {} minute(s) remaining)".format(member.id, hours, minutes))
        else:
            # Format embed
            harvest_embed = copy.deepcopy(self.embeds["harvest"])
            harvest_embed["thumbnail"]["url"] = harvest_embed["thumbnail"]["url"].format(self.game_data["img_urls"][player.type])
            harvest_embed["fields"][0]["value"] = harvest_embed["fields"][0]["value"].format(self._convert_short_text(player.type), harvest_yield)
            
            # Send embed
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))
            await self.client.send_message(member, content=None, embed=discord.Embed().from_data(harvest_embed))

    async def produce(self, ctx, drink_type):
        # FUTURE: Turn this into class and save them (persistance over restarts, crashes, etc)
        
        # Ensure correct arguments are passed
        if drink_type == None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a drink type (either regular or mixed).")
            return

        # Get (discord) member object from context
        member = ctx.message.author
        drink_type = drink_type.lower()

        if not await self.is_player(member): return
        
        # Load player data
        player = await self.get_player(member.id)

        # Ensure user has access to the command
        if not player.farm_level > 0:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "You do not have access to this command yet. Check shop for details.")
            return

        # Ensure correct argument was passed
        if not drink_type in ["regular", "mixed"]:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please choose either a reguar or mixed drink.")
            return
        
        if not player.farm_level > 2 and drink_type == "mixed":
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "You do not have access to mixed drinks yet. Check shop for details.")
            return

        if not ctx.message.channel.is_private:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))

        emojis = {"\U0001F34E": "apple", "\U0001F34C": "banana", "\U0001F347": "grape"}
        confirmation_check = lambda msg: True if msg.content.lower() in ['yes', 'no'] else False
        def production_check(msg):
                try:
                    if int(msg.content)>0:
                        return True
                except ValueError:
                    if msg.content == "all":
                        return True
                    return False

        if drink_type == "regular":
            # Do regular dialogue
            
            await self.client.send_typing(member)
            msg = await self.client.send_message(member, "Which fruit would you like to use?")
            await self.client.add_reactions(msg, emojis.keys())
            emoji_res = await self.client.wait_for_reaction(emoji=list(emojis.keys()), message=msg, user=member)

            # Do calculations
            max_drink = player.inventory[emojis[emoji_res.reaction.emoji]] / self.game_data["juice_upgrades"]["regular"]["fruit_req"][0]
            max_drink = int(max_drink)

            if max_drink == 0:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "You do not have enough {} to refine.".format(emoji_res.reaction.emoji))
                return

            level = 0 # Regular
            # If a user has unlocked quality products, ask if they want to make them.
            if player.farm_level > 1:    
                quality_hour, quality_minute = divmod((self.game_data["juice_upgrades"]["quality"]["refine_time"] // 60), 60)
                regular_hour, regular_minute = divmod((self.game_data["juice_upgrades"]["regular"]["refine_time"] // 60), 60)
                
                await self.client.send_typing(member)
                msg = await self.client.send_message(member, 
                "Would you like to make higher quality drinks? These will take {} hour(s) {} minute(s). (Regular drinks take {} hour(s) {} minute(s))".format(
                    quality_hour, quality_minute, regular_hour, regular_minute
                ))
                confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=await self.client.start_private_message(member))

                if confirmation.content == "yes":
                    level = 1 # Quality
                    await self.client.send_typing(member)
                    await self.client.send_message(member, "Quality set to high.")

            await self.client.send_typing(member)
            msg = await self.client.send_message(member, "This will make {quality} {name} juice. The conversion rate is {rate}.\n"
                "You can produce a max of {max} {quality} {name} juice. Type `all` to produce this many, or enter a specific number.".format(
                    quality = "regular" if level == 0 else "quality",
                    name = emojis[emoji_res.reaction.emoji],
                    rate = "{}x{}=\U0001F943x1".format(
                        emoji_res.reaction.emoji,
                        self.game_data["juice_upgrades"]["regular"]["fruit_req"][0]),
                    max = max_drink
                ))
            quantity_res = await self.client.wait_for_message(check=production_check, author=member, channel=await self.client.start_private_message(member))

            if quantity_res.content == "all":
                quantity = max_drink
            else:
                quantity = int(quantity_res.content)

            production = {
                "time": self.game_data["juice_upgrades"]["regular"]["refine_time"] if level == 0 else self.game_data["juice_upgrades"]["quality"]["refine_time"],
                "fruit_type": [emojis[emoji_res.reaction.emoji]],
                "drink_quantity": quantity,
                "fruit_cost": (self.game_data["juice_upgrades"]["regular"]["fruit_req"][0] * quantity,),
                "unit_sell_price": self.game_data["juice_upgrades"]["regular"]["item_price"] if level == 0 else self.game_data["juice_upgrades"]["quality"]["item_price"]
            }

            # Final confirmation check
            embed = copy.deepcopy(self.embeds["production_confirmation"])
            embed["fields"][0]["value"] = embed["fields"][0]["value"].format(emoji_res.reaction.emoji)
            embed["fields"][1]["value"] = embed["fields"][1]["value"].format("Regular" if level == 0 else "Quality")
            embed["fields"][2]["value"] = embed["fields"][2]["value"].format(production["unit_sell_price"] * production["drink_quantity"])
            embed["fields"][3]["value"] = embed["fields"][3]["value"].format(emoji_res.reaction.emoji, production["fruit_cost"][0])
            
            hours, minutes = divmod((production["time"] // 60), 60)
            embed["fields"][4]["value"] = embed["fields"][4]["value"].format(hours, minutes)

            await self.client.send_typing(member)
            await self.client.send_message(member, embed=discord.Embed().from_data(embed))
            await self.client.send_message(member, "Would you like to start production?")
            confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=await self.client.start_private_message(member))

            if confirmation.content == "yes":
                await self.client.send_typing(member)
                await self.client.send_message(member, "Production started.")
            else:
                await self.client.send_typing(member)
                await self.client.send_message(member, "Production canceled.")
                return

        else:    
            # Do mixed dialogue
            # Get 1st fruit
            await self.client.send_typing(member)
            msg = await self.client.send_message(member, "Which 1st fruit would you like to use?")
            await self.client.add_reactions(msg, emojis.keys())
            fruit1_res = await self.client.wait_for_reaction(emoji=list(emojis.keys()), message=msg, user=member)

            # Get 2nd fruit
            await self.client.send_typing(member)
            msg = await self.client.send_message(member, "Which 2nd fruit would you like to use?")
            await self.client.add_reactions(msg, emojis.keys())
            fruit2_res = await self.client.wait_for_reaction(emoji=list(emojis.keys()).remove(fruit1_res.reaction.emoji), message=msg, user=member)

            level = 0 # Regular
            # If a user has unlocked quality products, ask if they want to make them.
            if player.farm_level > 3:    
                quality_hour, quality_minute = divmod((self.game_data["juice_upgrades"]["quality_mixed"]["refine_time"] // 60), 60)
                regular_hour, regular_minute = divmod((self.game_data["juice_upgrades"]["mixed"]["refine_time"] // 60), 60)
                
                await self.client.send_typing(member)
                msg = await self.client.send_message(member, 
                "Would you like to make higher quality mixed drinks? These will take {} hour(s) {} minute(s). (Regular drinks take {} hour(s) {} minute(s))".format(
                    quality_hour, quality_minute, regular_hour, regular_minute
                ))
                confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=await self.client.start_private_message(member))

                if confirmation.content == "yes":
                    level = 1 # Quality
                    await self.client.send_typing(member)
                    await self.client.send_message(member, "Quality set to high.")
  
            # Get max drink
            if level == 1:
                # Account for quality mixed
                calculated_amounts = []
                
                # 1st Fruit
                calculated_amounts.append(
                    player.inventory[emojis[fruit1_res.reaction.emoji]] / self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][0]
                )

                # 2nd Fruit
                calculated_amounts.append(
                    player.inventory[emojis[fruit2_res.reaction.emoji]] / self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][1]
                )
                
                max_drink = int(min(calculated_amounts))
            else:
                # Account for regular mixed
                calculated_amounts = []
                
                # 1st Fruit
                calculated_amounts.append(
                    player.inventory[emojis[fruit1_res.reaction.emoji]] / self.game_data["juice_upgrades"]["mixed"]["fruit_req"][0]
                )

                # 2nd Fruit
                calculated_amounts.append(
                    player.inventory[emojis[fruit2_res.reaction.emoji]] / self.game_data["juice_upgrades"]["mixed"]["fruit_req"][1]
                )
                
                max_drink = int(min(calculated_amounts))

            if max_drink == 0:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "You do not have enough {} to refine.".format(emoji_res.reaction.emoji))
                return
            
            await self.client.send_typing(member)
            msg = await self.client.send_message(member, "This will make {quality} {name} juice. The conversion rate is {rate}.\n"
                "You can produce a max of {max} {quality} {name} juice. Type `all` to produce this many, or enter a specific number.".format(
                    quality = "regular mixed" if level == 0 else "quality mixed",
                    name = emojis[fruit1_res.reaction.emoji] + " " + emojis[fruit2_res.reaction.emoji],
                    rate = "{}x{} + {}x{} =\U0001F943x1".format(
                        fruit1_res.reaction.emoji,
                        self.game_data["juice_upgrades"]["mixed"]["fruit_req"][0] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][0],
                        fruit2_res.reaction.emoji,
                        self.game_data["juice_upgrades"]["mixed"]["fruit_req"][1] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][1]),
                    max = max_drink
                ))
            quantity_res = await self.client.wait_for_message(check=production_check, author=member, channel=await self.client.start_private_message(member))

            if quantity_res.content == "all":
                quantity = max_drink
            else:
                quantity = int(quantity_res.content)

            production = {
                "time": self.game_data["juice_upgrades"]["mixed"]["refine_time"] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["refine_time"],
                "fruit_type": [emojis[fruit1_res.reaction.emoji], emojis[fruit2_res.reaction.emoji]],
                "drink_quantity": quantity,
                "fruit_cost": (
                    (self.game_data["juice_upgrades"]["mixed"]["fruit_req"][0] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][0]) * quantity,
                    (self.game_data["juice_upgrades"]["mixed"]["fruit_req"][1] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["fruit_req"][1]) * quantity
                ),
                "unit_sell_price": self.game_data["juice_upgrades"]["mixed"]["item_price"] if level == 0 else self.game_data["juice_upgrades"]["quality_mixed"]["item_price"]
            }

            # Final confirmation check
            embed = copy.deepcopy(self.embeds["production_confirmation"])
            embed["fields"][0]["value"] = embed["fields"][0]["value"].format(fruit1_res.reaction.emoji+fruit2_res.reaction.emoji)
            embed["fields"][1]["value"] = embed["fields"][1]["value"].format("Regular mixed" if level == 0 else "Quality mixed")
            embed["fields"][2]["value"] = embed["fields"][2]["value"].format(production["unit_sell_price"] * production["drink_quantity"])
            embed["fields"][3]["value"] = embed["fields"][3]["value"].format(
                fruit1_res.reaction.emoji, 
                "{}\n{}x{}".format(
                    production["fruit_cost"][0],
                    fruit2_res.reaction.emoji,
                    production["fruit_cost"][1]
                )
            )
            
            hours, minutes = divmod((production["time"] // 60), 60)
            embed["fields"][4]["value"] = embed["fields"][4]["value"].format(hours, minutes)

            await self.client.send_typing(member)
            await self.client.send_message(member, embed=discord.Embed().from_data(embed))
            await self.client.send_message(member, "Would you like to start production?")
            confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=await self.client.start_private_message(member))

            if confirmation.content == "yes":
                await self.client.send_typing(member)
                await self.client.send_message(member, "Production started.")
            else:
                await self.client.send_typing(member)
                await self.client.send_message(member, "Production canceled.")
                return

        # By this line production (dict) should be defined
        
        # Sleep for time
        # await asyncio.sleep(production["time"]) # Actual command
        await asyncio.sleep(5) # For demonstration
        
        # Send message
        await self.client.send_message(member, "Your production request has finished. This has netted you :moneybag:x{}".format(
            production["unit_sell_price"] * production["drink_quantity"]
        ))
        # Update user profile
        for i, x in enumerate(production["fruit_type"]):
            player.inventory[x] -= production["fruit_cost"][i]
        player.money += production["unit_sell_price"] * production["drink_quantity"]

        player.save()
        
    async def sell(self, ctx, type_amount):
        member = ctx.message.author

        if type_amount is None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a type and an amount.")
            return

        if not await self.is_player(member): return

        player = await self.get_player(member.id)
        
        emojis = {"\U0001F34E": "apple", "\U0001F34C": "banana", "\U0001F347": "grape"}
        string_list = type_amount.split("x")
            
        # Ensure there is an emoji passed
        if emojis.get(string_list[0]) is None:
            # Create error
            print("Incorrect stuff")
            return

        # Ensure the amount is an int and is not less than 1
        try:
            quantity = int(string_list[1])

            if quantity < 1:
                raise ValueError
        except ValueError:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a correct number.")

        # Ensure the player has the amount they want to sell
        if not quantity <= player.inventory[emojis.get(string_list[0])]:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "You do not have enough {}.".format(string_list[0]))
            return

        # Calculate profit
        profit = quantity * self.game_data["fruit_price"]
        profit = int(profit)

        # Confirm with the user
        await self.client.send_typing(ctx.message.channel)
        await self.client.send_message(ctx.message.channel, "This will net you :moneybag:x{}".format(profit))

        await self.client.send_message(member, "Would you like to sell?")
        confirmation_check = lambda msg: True if msg.content.lower() in ['yes', 'no'] else False
        confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=ctx.message.channel)

        if confirmation.content == "yes":
            await self.client.send_message(ctx.message.channel, "You gained :moneybag:x{} for selling {}x{}".format(
                profit, string_list[0], quantity
            ))
        else:
            await self.client.send_message(ctx.message.channel, "Selling canceled :wastebasket:")
            return
        
        player.money += profit
        player.inventory[emojis.get(string_list[0])] -= quantity
        player.save()
    
    async def send_trade(self, ctx, recipient_id, request, offer):
        # Ensure recipient isn't blank
        if recipient_id is None: 
            await self.client.send_message(ctx.message.channel, "Please @ a player to send the trade to.")
            return

        # Get both member objects
        member = ctx.message.author
        recipient_id = recipient_id[2:-1]
        recipient = None

        # Ensure recipient isn't self
        if member.id == recipient_id:
            await self.client.send_message(ctx.message.channel, "You cannot trade with yourself.")
            return

        for x in self.client.get_all_members():
            if x.id == recipient_id:
                recipient = x
                break

        if recipient is None:
            await self.client.send_message(ctx.message.channel, content="Cannot find player.")

        # Ensure both members are part of the game
        if not await self.is_player(member): return
        if not await self.is_player(recipient, error_message="The mentioned person has not joined the game."): return

        emojis = {"\U0001F34E": "apple", "\U0001F34C": "banana", "\U0001F347": "grape", "\U0001F4B0": "money"}
        sender_player = await self.get_player(member.id)
        recipient_player = await self.get_player(recipient.id)

        # Ensure there is space in both users trade slots
        recipient_slot = None
        sender_slot = None
        
        for c, x in enumerate(recipient_player.in_trade):
            if x == 0:
                recipient_slot = c
                break
        else:
            await self.client.send_message(ctx.message.channel, "That player cannot recieve any more trade offers.")
            return

        for c, x in enumerate(sender_player.out_trade):
            if x == 0:
                sender_slot = c
                break
        else:
            await self.client.send_message(ctx.message.channel, "You cannot send any more trade offers.")
            return
        
        # Parse and/or aquire the arguments
        if request is not None and offer is not None:
            # Parse the arguments from single line command
            # TODO: Add this

            # Request
            request_list = request.split("x")
            
            if emojis.get(request_list[0]) is None:
                # Create error
                print("error")
                return None

            # Offer
            offer_list = offer.replace(" ", "").split("x")

            print(request_list, emojis.get(request_list[0]), request_list[1])

        else:
            # Get arguemnts from Trade dialogue
            
            def is_positive_int(msg):
                try:
                    if int(msg.content)>0: 
                        return True
                except ValueError:
                    return False

            # Request
            msg = await self.client.send_message(member, "What are you requesting?")
            await self.client.add_reactions(msg, emojis.keys())
            emoji_res = await self.client.wait_for_reaction(emoji=list(emojis.keys()), message=msg, user=member)

            msg = await self.client.send_message(member, "How many {} are you requesting?".format(emoji_res.reaction.emoji))
            quantity_res = await self.client.wait_for_message(check=is_positive_int, author=member, channel=await self.client.start_private_message(member))

            request = (emojis[emoji_res.reaction.emoji], int(quantity_res.content))

            # Offer
            msg = await self.client.send_message(member, "What are you offering?")
            await self.client.add_reactions(msg, emojis.keys())
            emoji_res = await self.client.wait_for_reaction(emoji=list(emojis.keys()), message=msg, user=member)

            msg = await self.client.send_message(member, "How many {} are you offering?".format(emoji_res.reaction.emoji))
            quantity_res = await self.client.wait_for_message(check=is_positive_int, author=member, channel=await self.client.start_private_message(member))

            offer = (emojis[emoji_res.reaction.emoji], int(quantity_res.content))

            # Check if player has what they offered
            if offer[0] == "money":
                if not sender_player.money >= offer[1]:
                    await self.client.send_message(member, "You do not have :moneybag:x{}. The trade has been canceled.".format(offer[1]))
                    return
            else:
                if not sender_player.inventory[offer[0]] >= offer[1]:
                    await self.client.send_message(member, "You do not have {}x{}. The trade has been canceled.".format(emoji_res.reaction.emoji, offer[1]))
                    return

        # Create trade
        sender_details = (member, member.name, sender_slot)
        recipient_details = (recipient, recipient.name, recipient_slot)

        trade = Trade(sender=sender_details, recipient=recipient_details, request=request, offer=offer)

        # Confirmation
        confirmation_trade_embed = trade.create_confirmation_embed(self.embeds["trade_confirmation"], )
        await self.client.send_message(member, embed=confirmation_trade_embed)
        
        await self.client.send_message(member, "Is this trade correct?")
        confirmation_check = lambda msg: True if msg.content.lower() in ['yes', 'no'] else False
        confirmation = await self.client.wait_for_message(check=confirmation_check, author=member, channel=await self.client.start_private_message(member))

        if confirmation.content == "yes":
            await self.client.send_message(member, "Trade sent :incoming_envelope:")
        else:
            await self.client.send_message(member, "Trade canceled :wastebasket:")
            return

        # Remove offer from sender's inventory to prevent overdrawing from inventory
        if offer[0] == "money":
            sender_player.money -= offer[1]
        else:
            sender_player.inventory[offer[0]] -= offer[1]

        # Add to players trade slots
        # Recipient Incoming (holds Trade object)
        recipient_player.in_trade[recipient_slot] = trade

        # Sender Outgoing (only holds details)
        sender_player.out_trade[sender_slot] = {
            "recipient_name": recipient.name,
            "recipient_id": recipient.id,
            "request": request,
            "offer": offer
        }

        # Recipient Incoming Trade Embed
        incoming_trade_embed = trade.create_incoming_embed(self.embeds["trade_incoming"])

        await self.client.send_message(recipient, embed=incoming_trade_embed)
        await self.client.send_message(recipient, 
        "Accept with `{command_prefix}accept {trade_slot}` or decline with `{command_prefix}decline {trade_slot}`".format(
            command_prefix = self.client.command_prefix, trade_slot = (recipient_slot+1)
        ))

        recipient_player.save()
        sender_player.save()
    
    async def accept_trade(self, ctx, trade_slot):
        # Load players into variables
        recipient_member = ctx.message.author
        sender_member = None

        if trade_slot is None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a trade slot.")
            return
        
        if not await self.is_player(recipient_member): return
        
        try:
            trade_slot = int(trade_slot)
        except ValueError:
            await self.client.send_message(ctx.message.channel, "Please select a trade slot between 1-4.")
        
        if not await self._within_slot_boundaries(trade_slot, recipient_member): return

        recipient_player = await self.get_player(recipient_member.id)
        sender_player = None

        # Ensure trade exists in slot
        trade_slot = trade_slot-1
        if not isinstance(recipient_player.in_trade[trade_slot], Trade):
            await self.client.send_message(recipient_member, "This slot does not contain an incoming trade.")
            return
        else:
            trade = recipient_player.in_trade[trade_slot]

        # Ensure recipient has request
        if trade.request[0] == "money":
            if not recipient_player.money >= trade.request[1]:
                await self.client.send_message(recipient_member, "You do not have {}x{}.".format(
                    ":moneybag:", trade.request[1]
                ))
                return
        else:
            if not recipient_player.inventory[trade.request[0]] >= trade.request[1]:
                await self.client.send_message(recipient_member, "You do not have {}x{}.".format(
                    ":{}:".format(self._convert_short_text(trade.request[0])), trade.request[1]
                ))
                return
        
        # Get sender member
        for x in self.client.get_all_members():
            if trade.sender == x.id:
                sender_member = x
        
        sender_player = await self.get_player(sender_member.id)

        # Remove trades from both players boxes
        recipient_player.in_trade[trade_slot] = 0
        sender_player.out_trade[trade.sender_slot] = 0
                
        # Update player inventories
        # Offer
        if trade.offer[0] == "money":
            recipient_player.money += trade.offer[1]
        else:
            recipient_player.inventory[trade.offer[0]] += trade.offer[1]

        # Request
        if trade.request[0] == "money":
            sender_player.money += trade.request[1]
            recipient_player.money -= trade.request[1]
        else:
            sender_player.inventory[trade.request[0]] += trade.request[1]
            recipient_player.inventory[trade.request[0]] -= trade.request[1]

        # Send message
        trade_message = "{}x{} for {}x{}.".format(
            ":{}:".format(self._convert_short_text(trade.request[0])), trade.request[1],
            ":{}:".format(self._convert_short_text(trade.offer[0])), trade.offer[1]
        )
        
        await self.client.send_message(recipient_member, "You accepted {}'s trade request: {}".format(
            sender_member.name, trade_message
        ))
        
        await self.client.send_message(sender_member, "{} has accepted your trade request: {}".format(
            recipient_member.name, trade_message))

        # Save players
        recipient_player.save()
        sender_player.save()

    async def decline_trade(self, ctx, trade_slot):
        # Load players into variables
        recipient_member = ctx.message.author
        sender_member = None
        
        if trade_slot is None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a trade slot.")
            return

        if not await self.is_player(recipient_member): return
        
        try:
            trade_slot = int(trade_slot)
        except ValueError:
            await self.client.send_message(ctx.message.channel, "Please select a trade slot between 1-4.")
        
        if not await self._within_slot_boundaries(trade_slot, recipient_member): return

        recipient_player = await self.get_player(recipient_member.id)
        sender_player = None

        # Ensure trade exists in slot
        trade_slot = trade_slot-1
        if not isinstance(recipient_player.in_trade[trade_slot], Trade):
            await self.client.send_message(recipient_member, content="This slot does not contain an incoming trade.")
            return
        else:
            trade = recipient_player.in_trade[trade_slot]

        # Get sender member
        for x in self.client.get_all_members():
            if trade.sender == x.id:
                sender_member = x
        
        sender_player = await self.get_player(sender_member.id)

        # Remove trades from both players boxes
        recipient_player.in_trade[trade_slot] = 0
        sender_player.out_trade[trade.sender_slot] = 0
        
        # Refund sender
        if trade.offer[0] == "money":
            sender_player.money += trade.offer[1]
        else:
            sender_player.inventory[trade.offer[0]] += trade.offer[1]

        # Send message
        trade_message = "{}x{} for {}x{}.".format(
            ":{}:".format(self._convert_short_text(trade.request[0])), trade.request[1],
            ":{}:".format(self._convert_short_text(trade.offer[0])), trade.offer[1]
        )
        
        await self.client.send_message(recipient_member, "You declined {}'s trade request: {}".format(
            sender_member.name, trade_message
        ))
        
        await self.client.send_message(sender_member, "{} has declined your trade request: {}".format(
            recipient_member.name, trade_message))

        # Save players
        recipient_player.save()
        sender_player.save()

    async def get_profile(self, ctx):
        # Get (discord) member object from context
        member = ctx.message.author 

        # Ensure the user has already joined
        if not await self.is_player(member): return
        
        player = await self.get_player(member.id)

        # Format profile
        thumbnail = member.avatar_url if not member.avatar_url == "" else member.default_avatar_url
        profile_embed = player.create_profile_embed(
            (copy.deepcopy(self.embeds["profile"]), copy.deepcopy(self.embeds["profile_trades"])),
            member.name, thumbnail
        )
        
        # Send embed
        await self.client.send_typing(ctx.message.channel)
        await self.client.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))
        for x in profile_embed:
            await self.client.send_message(member, content=None, embed=x)
    
    async def upgrade(self, ctx, stat):
        # Get (discord) member object from context
        member = ctx.message.author
        
        if stat is None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a stat you want to upgrade.")
        
        stat = stat.lower()

        # Ensure the user has already joined
        if not await self.is_player(member): return
        
        # Load player
        player = await self.get_player(member.id)

        if not stat in ["size", "multiplier", "farm"]:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, "Please enter a correct stat. See help or shop for details.")
            return

        # Upgrade stat
        if stat == "size":
            # Check if player has money
            cost = player.calculate_upgrade("size")

            if not cost <= player.money:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "You do not have enough money")
                return

            # Change variables in player
            prior_yield = player.upgrades["size"]
            player.upgrades["size"] = player.calculate_upgrade("size", price=False)
            player.money -= player.calculate_upgrade("size")
            player.upgrade_levels["size"] += 1
            
            
            await self.client.send_message(member, "Farm size was upgraded from {} yield to {} yield.".format(prior_yield, player.upgrades["size"]))

        elif stat == "multiplier":
            # Check if player has money
            cost = player.calculate_upgrade("multiplier")
            
            if not cost <= player.money:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "You do not have enough money.")
                return
            
            # Change variables in player
            prior_yield = player.upgrades["multiplier"]
            player.upgrades["multiplier"] = player.calculate_upgrade("multiplier", price=False)
            player.money -= player.calculate_upgrade("multiplier")
            player.upgrade_levels["multiplier"] += 1

            await self.client.send_message(ctx.message.channel, "Multiplier was upgraded from x{} to x{}.".format(prior_yield, player.upgrades["multiplier"]))
        
        else:
            if player.farm_level == 4:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "Farm Utilites cannot be leveled any higher.")
                return
            
            juice_upgrades_name = self.game_data["juice_upgrades"]["id_to_name"][str(player.farm_level+1)]

            if not self.game_data["juice_upgrades"][juice_upgrades_name]["unlock_price"] <= player.money:
                await self.client.send_typing(ctx.message.channel)
                await self.client.send_message(ctx.message.channel, "You do not have enough money.")
                return
            
            player.farm_level += 1
            player.upgrades["farm"].append(self.game_data["juice_upgrades"][juice_upgrades_name]["name"])
            player.money -= self.game_data["juice_upgrades"][juice_upgrades_name]["unlock_price"]

            await self.client.send_message(ctx.message.channel, "Farm Utilities was upgraded from level {} to level {}.".format(player.farm_level-1, player.farm_level))
        
        player.save()

    async def get_shop(self, ctx):
        # Get (discord) member object from context
        member = ctx.message.author

        # Ensure the user has already joined
        if not await self.is_player(member): return

        player = await self.get_player(member.id)
        upgrades_embed = player.create_shop_embed(
            copy.deepcopy(self.embeds["shop"]), member, self.client.command_prefix, self.game_data["juice_upgrades"]
        )

        # Send embed
        await self.client.send_typing(ctx.message.channel)
        for x in upgrades_embed:
            await self.client.send_message(member, content=None, embed=x)
        
    async def get_leaderboard(self, ctx=None, daily=False):
        if ctx is not None and self.leaderboard_embed is not None:
            await self.client.send_message(ctx.message.channel, embed=self.leaderboard_embed)
            return
        
        # Generate leaderboard embed
        # Load all player
        player_scores = []
        
        for x in self.players.list:
            player = await self.get_player(x)
            # Get discord.Member object
            member = None
            for x in self.client.get_all_members():
                if x.id == player.id:
                    member = x
            score = (member, player.money)
            player_scores.append(score)

        # print("Unsorted: ", player_scores)
        player_scores = sorted(player_scores, key=lambda n: n[1], reverse=True)
        # print("Sorted: ", player_scores)

        # Create new/Overwrite self.leaderboard_embed
        leaderboard_embed = discord.Embed(title="Leaderboard", color=discord.Color(3060770))
        
        for c, x in enumerate(player_scores):
            if c > 9:
                break
            leaderboard_embed.add_field(name="({}) {}".format(c+1, x[0].name), value="Points: {}".format(x[1]))

        self.leaderboard_embed = leaderboard_embed
        
        if ctx is not None:
            await self.client.send_typing(ctx.message.channel)
            await self.client.send_message(ctx.message.channel, embed=leaderboard_embed)
        
        if daily:
            leaderboard_channel = self.client.get_channel(self.leaderboard_channel)

            await self.client.send_message(leaderboard_channel, embed=discord.Embed(
                title="Current Leaderboard", color=discord.Color(3060770), timestamp=datetime.datetime.now()))

            for c, x in enumerate(player_scores):
                if c > 2:
                    break
                
                embed = discord.Embed(title="({}) {}".format(c+1, x[0].name), color=discord.Color(3060770))
                thumbnail = x[0].avatar_url if not x[0].avatar_url == "" else x[0].default_avatar_url
                embed.set_thumbnail(url=thumbnail)
                embed.add_field(name="Points", value=x[1])
                await self.client.send_message(leaderboard_channel, embed=embed)

            await self.client.send_message(leaderboard_channel, embed=discord.Embed(
                title="", color=discord.Color(3060770), description="Type `{}leaderboard` for the full leaderboard.".format(self.client.command_prefix)
            ))
      
    async def leaderboard_day_loop(self):
        while True:
            target = datetime.datetime.combine(datetime.datetime.today(), datetime.time.max)
            current_time = datetime.datetime.now()
            delta = int((target - current_time).total_seconds())

            print("leaderboard")
            log.debug("sleeping for {} seconds".format(delta))
            await self.get_leaderboard(daily=True)

            await asyncio.sleep(delta)

    # Trade
    # ---------------------------

    async def _within_slot_boundaries(self, trade_slot, member):
        # Ensure trade slot is between 1-4
        if trade_slot>4 or trade_slot<1:
            await self.client.send_message(member, content="Please select a trade slot between 1-4.")
            return False
        return True

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

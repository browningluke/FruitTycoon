# Internal Python Moduels
import asyncio
import logging
import sys
import os

# Imported (External) Python Modules
import discord
from discord.ext import commands

# Other project files
from .player import Player

# Misc
from .constants import VERSION
from .json import Json

log = logging.getLogger("root")
log.debug("discordClient.py loaded")


class DiscordClient(commands.Bot):

    def __init__(self, prefix, game_data, game=None):
        """Creates a client to interface with Discord.
        
        Arguments:
            prefix {String} -- The prefix to identify a message as a command.
            game_data {Dict} -- A Dictionary containing game settings.
        
        Keyword Arguments:
            game {GameManager} -- A reference to a GameManager instance. (default: {None})
        """
    
        # Create instance of superclass 
        super(DiscordClient, self).__init__(command_prefix=prefix)

        self.game = game
        self.loop = None

        # Instantiate Embeds
        self.help_embed = None
        self.admin_embed = None

        # Defined in game_data.json
        self.game_data = game_data
        self.embeds = self.game_data["embeds"]
        self.fruit_types = self.game_data["fruits"]

        # Create commands
        self.remove_command("help")
        self.create_user_commands()
        self.create_admin_commands()
        self.help_embed = self.create_help_embed()

        @self.event
        async def on_ready():
            await self.setup_bot()

        # @self.event
        # async def on_message(message):
        #     await self.process_commands(message)

    async def setup_bot(self):
        """Once bot is ready, do other stuff."""
        
        log.info("Connected Successfully. FruitTycoon v{}".format(VERSION))
        
        app_info = await self.application_info()
        log.info('\nBot id: {}\nBot name: {}'.format(app_info.id, app_info.name))

        log.info("\nServers:")
        for x in self.servers:
            log.info(" - {}/{}\n".format(x.id, x.name))

        log.info("Bound text channels:\n - None")
        log.info("\nOptions:\n  Command prefix: {}\n".format(self.command_prefix))
        
        await self.change_presence(game=discord.Game(name="{}help".format(self.command_prefix)))  

        # Start leaderboard loop
        asyncio.ensure_future(self.game.leaderboard_day_loop(), loop=self.loop)      

    ##
    ## Helper functions
    ##

    @staticmethod
    def format_embed(embed, title=None, description=None, footer=None):
        """Formats embed from substitution list."""
        if title is not None:
            embed['title'] = embed['title'].format(title)
        if description is not None:
            embed['description'] = embed['description'].format(description)
        if footer is not None:
            embed['footer']['text'] = embed['footer']['text'].format(footer)
        return embed

    def _check_types(self, raw):
        if raw is None: return False
        if raw.lower() in self.fruit_types: return True
 
    def create_user_commands(self):
        """Create commands users can use."""
       
        @self.command(pass_context=True, description="help", help="[help]")
        async def help(ctx):
            await self.send_typing(ctx.message.channel)
            await self.send_message(ctx.message.author, embed=self.help_embed)
            await self.send_message(ctx.message.channel, "Sent to your DMs :e_mail:")

        @self.command(pass_context=True, description="join", help="[join]")
        async def join(ctx, fruit_type=None):
            """Add the user to the game"""
            member = ctx.message.author # Get (discord) member object from context
            
            # Ensure the user had not already joined
            if await self.game.get_player(member.id) is not None: 
                await self.send_message(member, content="You have already joined the game.")
                return

            # Ensure the user has entered a valid fruit type
            if fruit_type is None or not self._check_types(fruit_type):
                await self.send_message(ctx.message.channel, "<@{}> Please enter a valid fruit type. They are:\n- {}".format(member.id, '\n- '.join(self.fruit_types)))
                return

            # Send user welcome embed
            join_embed = self.format_embed(self.embeds["join"], title=member.name, description=member.name)

            await self.send_typing(ctx.message.channel)
            await self.send_message(member, content=None, embed=discord.Embed().from_data(join_embed))
            await self.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))
            await self.send_message(member, content="You've chosen :{}:. We'll plant your first lot for you. Run the harvest command in {} hours.".format("grapes" if fruit_type == "grape" else fruit_type, "2"))
            
            # Add user to PlayerIndex
            await self.game.join_game(ctx, fruit_type)

        @self.command(pass_context=True, description="harvest", help="[harvest]")
        async def harvest(ctx):
            member = ctx.message.author # Get (discord) member object from context

            # Ensure the user has already joined
            if await self.game.get_player(member.id) is None: 
                await self.send_message(member, content="You have to join the game to run this command.")
                return

            # Harvest fruit
            harvest_details = await self.game.harvest(member.id)
            
            # Send message
            if not harvest_details['time_valid']:
                hours, minutes = divmod((harvest_details['time_remaining'] // 60), 60) # Convert seconds to minutes, then calculate hours & minutes
                await self.send_typing(ctx.message.channel)
                await self.send_message(ctx.message.channel, "<@{}>, your fruit has not fully grown. ({} hour(s) {} minute(s) remaining)".format(member.id, hours, minutes))
            else:
                # Format embed
                harvest_embed = self.embeds["harvest"]
                harvest_embed["thumbnail"]["url"] = harvest_embed["thumbnail"]["url"].format(self.game_data["img_urls"][harvest_details["type"]])
                harvest_embed["fields"][0]["value"] = harvest_embed["fields"][0]["value"].format("grapes" if harvest_details["type"] == "grape" else harvest_details["type"], harvest_details["harvest_yield"])
                
                # Send embed
                await self.send_typing(ctx.message.channel)
                await self.send_message(member, content=None, embed=discord.Embed().from_data(harvest_embed))
    
        @self.command(pass_context=True, description="produce", help="[produce]")
        async def produce(ctx, quantity, fruit1, fruit2):
            # Load player data

            # Check what upgrade they have

            # Produce that, and start timer
            
            pass

        @self.command(pass_context=True, description="trade", help="[trade]")
        async def trade(ctx, quantity, recipient):
            pass

        @self.command(pass_context=True, description="profile", help="[profile]")
        async def profile(ctx):
            member = ctx.message.author # Get (discord) member object from context

            # Ensure the user has already joined
            if await self.game.get_player(member.id) is None: 
                await self.send_message(member, content="You have to join the game to run this command.")
                return

            # Create profile embed
            profile_embed = await self.game.get_profile(member, self.embeds["profile"])

            # Send embed
            await self.send_typing(ctx.message.channel)
            await self.send_message(member, content=None, embed=discord.Embed().from_data(profile_embed))

        @self.command(pass_context=True, description="upgrade", help="[upgrade]")
        async def upgrade(ctx):
            pass

        @self.command(pass_context=True, description="leaderboard", help="[leaderboard]")
        async def leaderboard(ctx):
            pass
    
    def create_admin_commands(self):
        """Create commands admins can use."""
        
        @self.group(pass_context=True, description="admin", help="[admin]")
        async def admin(ctx):
            if ctx.invoked_subcommand is None:
                await self.send_message(ctx.message.channel, "Please enter a valid subcommand.")

        @admin.command(pass_context=True, description="help", help="[help]")
        async def help(ctx, description="help", help="[help]"):            
            await self.send_typing(ctx.message.channel)
            await self.send_message(ctx.message.author, embed=self.admin_embed)
            await self.send_message(ctx.message.channel, "Sent to your DMs :e_mail:")

        @admin.command(pass_context=True, description="remove_player", help="[remove_player]")
        async def removePlayer(ctx, pid):
            """Add the user to the game"""
            member = ctx.message.author # Get (discord) member object from context
            
            # Ensure the user had not already joined
            if await self.game.get_player(member.id) is None:
                await self.send_message(member, content="Player does not exist.")
                return
            
            # Add user to PlayerIndex
            await self.game.remove_player(member.id)

        @admin.command(pass_context=True, description="print_list", help="[print_list]")
        async def print_list(ctx):
            await self.send_message(ctx.message.channel, content=str(self.game.players.list))

        @admin.command(pass_context=True, description="load_player", help="[load_player]")
        async def load_player(ctx, pid):
            player = await self.game.get_player(pid)
            print(player.__dict__)
        
        @admin.command(pass_context=True, description="reset", help="[reset]")
        async def reset(ctx):
            pass

        @admin.command(pass_context=True, description="ping", help="[ping]")
        async def ping(ctx):
            pass

        @admin.command(pass_context=True, description="reboot", help="[reboot]")
        async def reboot(ctx):
            await self.logout()
            os.system('cls')
            os.execv(sys.executable, ['python'] + sys.argv)

        @admin.command(pass_context=True, description="exit", help="[exit]")
        async def exit(ctx):
            await self.send_message(ctx.message.channel, "Powering down")
            await self.logout()
            log.info("Logged out")
            self.loop.stop()
            os._exit(1)

    def create_admin_help_embed(self, mixin):
        """Creates a discord.Embed object for the admin help command.
        
        Arguments:
            mixin {Tuple (name, GroupMixin)} -- A GroupMixin for the admin commands.
        """

        admin_embed = discord.Embed(title="Admin Commands", color=3060770)
        column_strings = {
            "command": "",
            "description": "",
            "arguments": ""
        }

        for cmd in mixin[1].commands.items():
            column_strings["command"] += "{prefix}admin {command}\n\n".format(prefix=self.command_prefix, command=cmd[0])
            column_strings["description"] += "{description}\n\n".format(description=cmd[1].description)
            column_strings["arguments"] += "{arguments}\n\n".format(arguments=cmd[1].help)

        for x in column_strings.keys():
            admin_embed.add_field(name=x.title(), value=column_strings[x], inline=True)
        
        self.admin_embed = admin_embed

    def create_help_embed(self):
        """Create a discord.Embed object for the help command.
        
        Returns:
            {Embed} -- Returns an embed containing information about all user commands.
        """

        help_embed = discord.Embed(title="Commands", color=3060770)
        column_strings = {
            "command": "",
            "description": "",
            "arguments": ""
        }

        # Add command name, descriptions and arguments to their respective string for every command 
        for cmd in self.commands.items():
            # Add admin group to admin embed list
            if cmd[0] == "admin":
                self.create_admin_help_embed(cmd)
                continue

            column_strings["command"] += "{prefix}{command}\n\n".format(prefix=self.command_prefix, command=cmd[0])
            column_strings["description"] += "{description}\n\n".format(description=cmd[1].description)
            column_strings["arguments"] += "{arguments}\n\n".format(arguments=cmd[1].help)
        
        # Add columns to embed
        for x in column_strings.keys():
            help_embed.add_field(name=x.title(), value=column_strings[x], inline=True)

        return help_embed
            
    def start_bot(self, token):
        self.loop = asyncio.get_event_loop()

        log.info("Bot starting")
        try:
            while True:
                try:
                    self.loop.create_task(self.start(token))
                    self.loop.run_forever()
                    
                    #self.loop.run_until_complete(self.start(token))
                except Exception as e:
                    log.critical(e)
        except KeyboardInterrupt:
            log.info("Logging out")
            self.loop.run_until_complete(self.logout())
            log.info("Logged out")
        except Exception as e:
            raise e


if __name__ == "__main__":
    DiscordClient('a.', None).start_bot("TOKEN")

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

    data_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/game_data.json"

    def __init__(self, prefix, game=None):
        super(DiscordClient, self).__init__(command_prefix=prefix)

        self.game = game

        self.loop = None
        self.help_embed = None
        self.admin_embed = None
        self.category_dict = None

        data = Json(DiscordClient.data_path)
        self.embeds = data.get("embeds")
        self.fruit_types = data.get("fruits")

        # Create commands
        self.remove_command("help")
        self.create_user_commands()
        self.create_admin_commands()
        self.setup_help()

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

    ##
    ### Helper functions
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
       
        @self.command(pass_context=True)
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
                print(self._check_types(fruit_type))
                return

            # Send user welcome embed
            join_embed = self.format_embed(self.embeds["join"], title=member.name, description=member.name)

            await self.send_typing(ctx.message.channel)
            await self.send_message(member, content=None, embed=discord.Embed().from_data(join_embed))
            await self.send_message(ctx.message.channel, "<@{}>, check your DMs. :incoming_envelope:".format(member.id))
            await self.send_message(member, content="You've chosen {}. We'll plant your first lot for you. Run the harvest command in {} hours.".format(fruit_type, "2"))
            
            # Add user to PlayerIndex
            await self.game.join_game(ctx, fruit_type)

        @self.command(pass_context=True)
        async def harvest(ctx):
            pass
    
        @self.command(pass_context=True)
        async def produce(ctx, quantity, fruit1, fruit2):
            pass

        @self.command(pass_context=True)
        async def trade(ctx, quantity, recipient):
            pass

        @self.command(pass_context=True)
        async def profile(ctx):
            pass

        @self.command(pass_context=True)
        async def upgrade(arguments):
            pass

        @self.command(pass_context=True)
        async def leaderboard(ctx):
            pass
    
    def create_admin_commands(self):
        """Create commands admins can use."""
        
        @self.group(pass_context=True)
        async def admin(ctx):
            if ctx.invoked_subcommand is None:
                await self.send_message(ctx.message.channel, "Please enter a valid subcommand.")

        @admin.command(pass_context=True, description="", help="[id]")
        async def removePlayer(ctx, pid):
            """Add the user to the game"""
            member = ctx.message.author # Get (discord) member object from context
            
            # Ensure the user had not already joined
            if await self.game.get_player(member.id) is None:
                await self.send_message(member, content="Player does not exist.")
                return
            
            # Add user to PlayerIndex
            await self.game.remove_player(member.id)

        @admin.command(pass_context=True, description="", help="[id]")
        async def print_list(ctx):
            await self.send_message(ctx.message.channel, content=str(self.game.players.list))

        @admin.command(pass_context=True, description="", help="[id]")
        async def load_player(ctx, pid):
            player = await self.game.get_player(pid)
            print(player.__dict__)
        
        @admin.command(pass_context=True, description="", help="[id]")
        async def reset(ctx):
            pass

        @admin.command(pass_context=True, description="", help="[id]")
        async def ping(ctx):
            pass

        @admin.command(pass_context=True, description="", help="[id]")
        async def reboot(ctx):
            await self.logout()
            os.system('cls')
            os.execv(sys.executable, ['python'] + sys.argv)

        @admin.command(pass_context=True, description="", help="[id]")
        async def exit(ctx):
            await self.send_message(ctx.message.channel, "Powering down")
            await self.logout()
            log.info("Logged out")
            sys.exit()

    def setup_help(self):
        pass

    def start_bot(self, token):
        self.loop = asyncio.get_event_loop()

        log.info("Bot starting")
        try:
            while True:
                try:
                    self.loop.run_until_complete(self.start(token))
                except Exception as e:
                    log.critical(e)
        except KeyboardInterrupt:
            log.info("Logging out")
            self.loop.run_until_complete(self.logout())
            log.info("Logged out")
        except Exception as e:
            raise e


if __name__ == "__main__":
    DiscordClient('a.').start_bot("TOKEN")

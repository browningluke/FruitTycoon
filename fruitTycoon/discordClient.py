# Internal Python Moduels
import asyncio
import logging

# Imported (External) Python Modules
import discord
from discord.ext import commands

# Misc
from .constants import VERSION

log = logging.getLogger("root")
log.debug("discordClient.py loaded")


class DiscordClient(commands.Bot):

    def __init__(self, prefix, game=None):
        super(DiscordClient, self).__init__(command_prefix=prefix)

        self.game = game

        self.loop = None
        self.help_embed = None
        self.admin_embed = None
        self.category_dict = None

        # Create commands
        self.remove_command("help")
        self.create_user_commands()
        self.create_admin_commands()
        self.setup_help()

        @self.event
        async def on_ready():
            await self.setup_bot()

        @self.event
        async def on_message(message):
            await self.process_commands(message)

    async def setup_bot(self):
        log.info("Connected Successfully. FruitTycoon v{}".format(VERSION))
        
        app_info = await self.application_info()
        log.info('\nBot id: {}\nBot name: {}'.format(app_info.id, app_info.name))

        log.info("\nServers:")
        for x in self.servers:
            log.info(" - {}/{}\n".format(x.id, x.name))

        log.info("Bound text channels:\n - None")
        log.info("\nOptions:\n  Command prefix: {}\n".format(self.command_prefix))
        
        await self.change_presence(game=discord.Game(name="{}help".format(self.command_prefix)))        

    def create_user_commands(self):
        @self.command(pass_context=True)
        async def ping(ctx):
            print("Pong")

    def create_admin_commands(self):
        @self.command(pass_context=True)
        async def stop(ctx):
            await self.logout()

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

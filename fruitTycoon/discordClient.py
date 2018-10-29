# import discord
from discord.ext import commands
import asyncio
import logging

log = logging.getLogger("root")
log.info("discordClient.py loaded")


class DiscordClient(commands.Bot):

    def __init__(self):
        super(DiscordClient, self).__init__(command_prefix="a.")

        # self.game =

        self.loop = None
        self.help_embed = None
        self.admin_embed = None
        self.category_dict = None

        self.setup_bot()

    def setup_bot(self):
        self.remove_command("help")
        self.define_commands()

        @self.event
        async def on_ready():
            print("Bot online")

    def define_commands(self):
        @self.command(pass_context=True)
        async def ping(ctx):
            print("Pong")

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
    DiscordClient().start_bot("TOKEN")

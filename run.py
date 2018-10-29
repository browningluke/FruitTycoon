import fruitTycoon.logger
log = fruitTycoon.logger.setup_custom_logger("root")

from fruitTycoon.discordClient import DiscordClient

def main():
    DiscordClient().start_bot("MzQ1MTA0NjgxOTEzMjg2NjU4.Drf1UQ.nDUXgy47CzcCnjVmrzUUrsogUQA")


if __name__ == '__main__':
    main()

import fruitTycoon.logger
log = fruitTycoon.logger.setup_custom_logger("root")

from fruitTycoon.game import GameManager

def main():
    GameManager().start_game()


if __name__ == '__main__':
    main()

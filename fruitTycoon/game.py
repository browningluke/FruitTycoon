class GameManager:

    def __init__(self):
        self.player_index = PlayerIndex()
        pass

    # Config
    # ---------------------------

    def load_config(self):
        pass

    # Players
    # ---------------------------

    # Player I/O

    async def get_player(self, player_id):
        pass

    # Game
    # ---------------------------

    async def join_game(self):
        pass

    async def harvest_fruit(self):
        pass

    async def get_profile(self):
        pass

    async def get_leaderboard(self):
        pass

    async def upgrade_stat(self):
        pass

    # Admin
    # ---------------------------

    async def reset_game(self):
        pass

    async def get_player_profile(self):
        pass


class PlayerIndex:

    file_location = ""

    def __init__(self):
        self.list = []

    async def load(self):
        pass

    async def save(self):
        pass

    async def add(self):
        pass

    async def remove(self):
        pass

    async def find(self):
        pass


class Player:

    def __init__(self):
        self.id = ""
        self.type = ""

        self.max_harvest_percent = 0
        self.max_harvest_percent = 0
        self.harvest_amount = 0
        self.planting_cost = 0

        self.money = 0
        self.last_harvest = 0
        self.inventory = {
            "apple": 0,
            "banana": 0,
            "grape": 0
        }

        self.upgrades = []

    async def save(self):
        pass

    async def load(self):
        pass

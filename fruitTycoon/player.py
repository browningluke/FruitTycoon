from .trade import Trade

class Player:

    def __init__(self, p_id, f_type):
        self.id = p_id
        self.type = f_type

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

        # Trades
        self.in_trade = []
        self.out_trade = []

    async def send_trade(self, player):
        trade = Trade(self, player)

        self.out_trade.append(trade)
        player.in_trade.append(trade)

        # trade

    async def save(self):
        pass

    async def load(self):
        pass
from random import randint


class Game:
    def __init__(self, player_count=10, length=3):
        self.players = [Player(f"P{i+1}") for i in range(player_count)]
        self.map = Map(length)
        self.impostor = None

        self.map.spawn_players(self)


class Player:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Map:
    def __init__(self, length=3):
        if length <= 0:
            raise ValueError("Map length must be positive.")

        self.map = [[[] for _ in range(length)] for _ in range(length)]

    def spawn_players(self, game):
        for player in game.players:
            x = randint(0, len(self.map) - 1)
            y = randint(0, len(self.map) - 1)

            self.map[x][y].append(player)

    def print_map(self):
        for row in self.map:
            line = []

            for cell in row:
                if not cell:
                    line.append(".")
                else:
                    line.append(",".join(player.name for player in cell))

            print(" | ".join(f"{cell:^10}" for cell in line))


def print_all_players(game):
    for player in game.players:
        print(player.name)
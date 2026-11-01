
from random import randint, choice


class Game:
    def __init__(self, player_count=5, length=3):
        if player_count < 2:
            raise ValueError("Need at least 2 players.")

        self.players = [Player(f"P{i+1}") for i in range(player_count)]

        self.map = Map(length)
        self.impostor = choice(self.players)
        self.impostor.is_impostor = True

        self.in_meeting = False
        self.frame = 0

        self.map.spawn_players(self)

    def record_sightings(self):
        for observer in self.players:
            if not observer.alive or observer.position is None:
                continue

            x, y = observer.position

            for target in self.map.map[x][y]:
                if target == observer:
                    continue

                observer.memory["sightings"].append({
                    "player": target.name,
                    "frame": self.frame,
                    "cell": observer.position
                })
    def get_tod_range(self, body, investigator):
        if body.discovery_frame is None:
            return None

        last_seen_frames = [
            sighting["frame"]
            for sighting in investigator.memory["sightings"]
            if sighting["player"] == body.player.name
            and sighting["frame"] <= body.discovery_frame
        ]

        if not last_seen_frames:
            return {
                "earliest": None,
                "latest": body.discovery_frame
            }

        last_seen = max(last_seen_frames)

        return {
            "earliest": last_seen,
            "latest": body.discovery_frame
        }

    @property
    def impostors(self):
        return sum(
            player.alive and player.is_impostor
            for player in self.players
        )

    @property
    def crewmates(self):
        return sum(
            player.alive and not player.is_impostor
            for player in self.players
        )

class Meeting:
    def __init__(self, game, body):
        self.game = game
        self.body = body

        self.shared_sightings = []
        self.statements = []


class Player:
    def __init__(self, name):
        self.name = name
        self.is_impostor = False
        self.alive = True
        self.position: tuple[int, int] | None = None

        self.memory = {
            "sightings": []
        }

    def __repr__(self):
        return self.name

class Body:
    def __init__(self, player, position, death_frame):
        self.player = player
        self.position = position

        # Ground truth: exact frame the player died.
        self.death_frame = death_frame

        # Investigation information:
        # None until a crewmate discovers the body.
        self.discovery_frame = None
        self.reported_by = None

    def __repr__(self):
        return f"Body({self.player.name}, {self.position})"

class Map:
    def __init__(self, length=3):
        if length < 2:
            raise ValueError("Map length must be at least 2.")

        self.length = length

        self.map = [
            [[] for _ in range(length)]
            for _ in range(length)
        ]

        self.bodies = []

    def spawn_players(self, game):
        for player in game.players:
            x = randint(0, self.length - 1)
            y = randint(0, self.length - 1)

            player.position = (x, y)
            self.map[x][y].append(player)

    def get_neighbors(self, position):
        x, y = position

        neighbors = [
            (x - 1, y),  # Up
            (x + 1, y),  # Down
            (x, y - 1),  # Left
            (x, y + 1)   # Right
        ]

        return [
            (nx, ny)
            for nx, ny in neighbors
            if 0 <= nx < self.length
            and 0 <= ny < self.length
        ]

    def move_players(self, game):
        # Calculate movements before applying them.
        movements = {}

        for player in game.players:
            if not player.alive:
                continue

            possible_moves = self.get_neighbors(player.position)
            movements[player] = choice(possible_moves)

        # Apply all movements.
        for player, new_position in movements.items():
            player.position = new_position

        self.rebuild_map(game)

    def rebuild_map(self, game):
        self.map = [
            [[] for _ in range(self.length)]
            for _ in range(self.length)
        ]

        for player in game.players:
            if player.alive:
                x, y = player.position
                self.map[x][y].append(player)

    def resolve_kills(self, frame):
        for x in range(self.length):
            for y in range(self.length):
                cell = self.map[x][y]

                impostors = [
                    p for p in cell
                    if p.is_impostor and p.alive
                ]

                crewmates = [
                    p for p in cell
                    if not p.is_impostor and p.alive
                ]

                if impostors and len(impostors) >= len(crewmates) and crewmates:

                    for player in crewmates:
                        player.alive = False

                        body = Body(
                            player=player,
                            position=(x, y),
                            death_frame=frame
                        )

                        self.bodies.append(body)

                        print(
                            f"FRAME {frame}: "
                            f"{player.name} was eliminated."
                        )

        self.rebuild_map_after_kills()

    def rebuild_map_after_kills(self):
        for row in self.map:
            for cell in row:
                cell[:] = [
                    player for player in cell
                    if player.alive
                ]

    def check_reports(self, game):
        for player in game.players:
            if not player.alive or player.is_impostor:
                continue

            for body in self.bodies:
                if body.discovery_frame is not None:
                    continue

                if player.position == body.position:
                    body.discovery_frame = game.frame
                    body.reported_by = player

                    print(
                        f"\n{player.name} reported "
                        f"{body.player.name}'s body!"
                    )

                    print(
                        f"Discovery frame: "
                        f"{body.discovery_frame}"
                    )

                    game.in_meeting = True
                    tod_range = game.get_tod_range(body, player)

                    if tod_range["earliest"] is None:
                        print("Estimated ToD: Unknown to earliest bound")
                    else:
                        print(
                            f"Estimated ToD: "
                            f"Frames {tod_range['earliest']} "
                            f"to {tod_range['latest']}"
                        )
                    return True

        return False

    def print_map(self):
        print("\n" + "=" * 60)

        for x, row in enumerate(self.map):
            line = []

            for y, cell in enumerate(row):
                names = [player.name for player in cell]

                for body in self.bodies:
                    if body.position == (x, y):
                        names.append(f"BODY:{body.player.name}")

                if not names:
                    names.append(".")

                line.append(",".join(names))

            print(" | ".join(f"{cell:^12}" for cell in line))

        print("=" * 60)


def print_all_players(game):
    for player in game.players:

        role = "Impostor" if player.is_impostor else "Crewmate"
        status = "Alive" if player.alive else "Dead"

        print(f"{player.name}: {role} | {status}")

def print_memories(game):
    for player in game.players:
        print(f"\n=== {player.name}'s MEMORY ===")

        for sighting in player.memory["sightings"]:
            print(
                f"Frame {sighting['frame']}: "
                f"Saw {sighting['player']} "
                f"at {sighting['cell']}"
            )
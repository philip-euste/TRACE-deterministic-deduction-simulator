
from random import randint, choice

from class_Body import Body


# ==========================================
# MAP
# ==========================================

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
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1)
        ]

        return [
            (nx, ny)
            for nx, ny in neighbors
            if 0 <= nx < self.length
            and 0 <= ny < self.length
        ]

    def move_players(self, game):
        movements = {}

        for player in game.players:
            if not player.alive or player.position is None:
                continue

            possible_moves = self.get_neighbors(
                player.position
            )

            movements[player] = choice(possible_moves)

        for player, new_position in movements.items():
            player.position = new_position

        self.rebuild_map(game)

    def rebuild_map(self, game):
        self.map = [
            [[] for _ in range(self.length)]
            for _ in range(self.length)
        ]

        for player in game.players:
            if player.alive and player.position is not None:
                x, y = player.position
                self.map[x][y].append(player)

    def resolve_kills(self, frame):
        kill_events = []

        for x in range(self.length):
            for y in range(self.length):

                cell = self.map[x][y]

                impostors = [
                    player
                    for player in cell
                    if player.is_impostor and player.alive
                ]

                crewmates = [
                    player
                    for player in cell
                    if not player.is_impostor and player.alive
                ]

                if (
                    impostors
                    and len(impostors) >= len(crewmates)
                    and crewmates
                ):
                    killer = impostors[0]

                    for player in crewmates:
                        player.alive = False

                        kill_events.append(
                            (killer, player)
                        )

                        body = Body(
                            player=player,
                            position=(x, y),
                            death_frame=frame,
                            killer=killer
                        )

                        self.bodies.append(body)

                        print(
                            f"FRAME {frame}: "
                            f"{player.name} was eliminated."
                        )

        # Keep dead players in their cells until sightings are recorded.
        return kill_events

    def rebuild_map_after_kills(self):
        for row in self.map:
            for cell in row:
                cell[:] = [
                    player
                    for player in cell
                    if player.alive
                ]

    def check_reports(self, game):
        living_players = [
            player
            for player in game.players
            if player.alive and player.position is not None
        ]

        players_by_position = {}

        for player in living_players:
            players_by_position.setdefault(
                player.position,
                []
            ).append(player)

        discovered_bodies = []

        for body in self.bodies:
            if body.discovered:
                continue

            players_here = players_by_position.get(
                body.position,
                []
            )

            eligible_reporters = [
                player
                for player in players_here
                if not (
                    player == body.killer
                    and game.frame == body.death_frame
                )
            ]

            if eligible_reporters:
                discovered_bodies.append(
                    (body, eligible_reporters[0])
                )

        if not discovered_bodies:
            return False

        for body, reporter in discovered_bodies:
            body.discovery_frame = game.frame
            body.reported_by = reporter

            print(
                f"\n{reporter.name} discovered "
                f"{body.player.name}'s body "
                f"at {body.position}!"
            )

        reporter = discovered_bodies[0][1]

        game.start_meeting(reporter)

        return True

    def print_map(self):
        print("\n" + "=" * 60)

        for x, row in enumerate(self.map):
            line = []

            for y, cell in enumerate(row):
                names = [
                    player.name
                    for player in cell
                ]

                for body in self.bodies:
                    if body.position == (x, y):
                        names.append(
                            f"BODY:{body.player.name}"
                        )

                if not names:
                    names.append(".")

                line.append(",".join(names))

            print(
                " | ".join(
                    f"{cell:^16}"
                    for cell in line
                )
            )

        print("=" * 60)

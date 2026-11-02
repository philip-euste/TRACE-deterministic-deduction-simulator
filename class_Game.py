
from random import sample

from class_Player import Player
from class_Map import Map
from class_Meeting import Meeting


# ==========================================
# GAME
# ==========================================

class Game:
    def __init__(
        self,
        player_count=5,
        length=3,
        murderer_count=1
    ):
        if player_count < 2:
            raise ValueError("Need at least 2 players.")

        if murderer_count < 1:
            raise ValueError("Need at least 1 murderer.")

        if murderer_count >= player_count:
            raise ValueError(
                "There must be at least 1 Crewmate."
            )

        self.players = [
            Player(f"P{i+1}")
            for i in range(player_count)
        ]

        self.map = Map(length)

        # Randomly select the configured number of murderers.
        self.murderers = sample(
            self.players,
            murderer_count
        )

        for murderer in self.murderers:
            murderer.is_impostor = True

        # Preserve the original singular attribute for compatibility.
        self.impostor = self.murderers[0]

        self.in_meeting = False
        self.meeting = None
        self.frame = 0

        self.map.spawn_players(self)

    def record_sightings(self, kill_events=None):
        # Convert kill events into a set for quick lookup.
        kill_events = set(kill_events or [])

        for observer in self.players:
            if not observer.alive or observer.position is None:
                continue

            x, y = observer.position

            for target in self.map.map[x][y]:
                if target == observer:
                    continue

                # Do not record the encounter that caused this observer's kill.
                if (observer, target) in kill_events:
                    continue

                observer.memory["sightings"].append({
                    "player": target.name,
                    "frame": self.frame,
                    "cell": observer.position
                })

    def start_meeting(self, reporter):
        self.in_meeting = True

        # Create the meeting and preserve its copy of all bodies.
        self.meeting = Meeting(
            game=self,
            reporter=reporter
        )

        # Remove bodies from the public map.
        self.map.bodies.clear()

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

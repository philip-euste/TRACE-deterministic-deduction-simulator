
from random import randint, choice

# ==========================================
# DEBUG / DISPLAY FUNCTIONS
# ==========================================

def print_all_players(game):
    for player in game.players:

        role = (
            "Impostor"
            if player.is_impostor
            else "Crewmate"
        )

        status = (
            "Alive"
            if player.alive
            else "Dead"
        )

        print(
            f"{player.name}: "
            f"{role} | {status}"
        )


def print_memories(game):
    for player in game.players:

        print(f"\n=== {player.name}'s MEMORY ===")

        for sighting in player.memory["sightings"]:
            print(
                f"Frame {sighting['frame']}: "
                f"Saw {sighting['player']} "
                f"at {sighting['cell']}"
            )

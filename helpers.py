from colorama import Fore, Style


# ==========================================
# DEBUG / DISPLAY FUNCTIONS
# ==========================================

def print_all_players(game):
    for player in game.players:

        if player.is_impostor:
            role = "Impostor"

            color = (
                Fore.LIGHTMAGENTA_EX
                if player.alive
                else Fore.MAGENTA
            )

        else:
            role = "Crewmate"

            color = (
                Fore.LIGHTBLUE_EX
                if player.alive
                else Fore.BLUE
            )

        status = (
            "Alive"
            if player.alive
            else "Dead"
        )

        print(
            f"{color}{Style.BRIGHT if player.alive else ''}"
            f"{player.name}: {role} | {status}"
            f"{Style.RESET_ALL}"
        )


def print_memories(game):
    for player in game.players:

        # Dead players' memories are not displayed.
        if not player.alive:
            continue

        print(f"\n=== {player.name}'s MEMORY ===")

        if not player.memory["sightings"]:
            print("No sightings recorded.")
            continue

        for sighting in player.memory["sightings"]:
            print(
                f"Frame {sighting['frame']}: "
                f"Saw {sighting['player']} "
                f"at {sighting['cell']}"
            )
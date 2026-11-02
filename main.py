from class_Game import Game
from helpers import print_all_players, print_memories

def main():
    game = Game(5, 2)

    print("=== PLAYERS ===")
    print_all_players(game)

    print("\n=== INITIAL MAP ===")
    game.map.print_map()

    # Main simulation loop.
    while (
        game.impostors < game.crewmates
        and not game.in_meeting
    ):
        input("\nPress Enter to advance one frame...")

        game.frame += 1

        print(
            f"\n\n========== FRAME {game.frame} =========="
        )

        # 1. Everyone moves.
        game.map.move_players(game)

        # 2. Record observations.
        game.record_sightings()

        # 3. Resolve kills.
        game.map.resolve_kills(game.frame)

        # 4. Check for body discoveries.
        game.map.check_reports(game)

        # 5. Print the public map.
        game.map.print_map()

    # Game termination or meeting.
    if game.in_meeting:
        print("\n=== MEETING STARTED ===")

        game.meeting.conduct()

    else:
        print("\n=== GAME OVER ===")

        if game.impostors >= game.crewmates:
            print("IMPOSTORS WIN!")

        else:
            print("CREWMATES WIN!")

    print("\n=== FINAL PLAYERS ===")
    print_all_players(game)

    print_memories(game)


if __name__ == "__main__":
    main()

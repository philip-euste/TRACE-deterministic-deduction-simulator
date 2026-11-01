
from helpers import Game, print_all_players, print_memories


def main():
    game = Game(5, 2)

    print("=== PLAYERS ===")
    print_all_players(game)

    print("\n=== INITIAL MAP ===")
    game.map.print_map()

    # Main simulation loop
    while game.impostors < game.crewmates:
        input()

        if game.in_meeting:
            break

        game.frame += 1

        print(f"\n\n========== FRAME {game.frame} ==========")


        # 1. Everyone moves.
        game.map.move_players(game)

        # 2. Record observations.
        game.record_sightings()

        # 3. Resolve kills.
        game.map.resolve_kills(game.frame)

        # 4. Print map.
        game.map.print_map()

        # 5. Check reports.
        game.map.check_reports(game)

    # Game termination
    if game.in_meeting:
        print("\n=== MEETING STARTED ===")
        print("Simulation paused. Awaiting meeting instructions.")

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

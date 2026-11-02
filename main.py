
from class_Game import Game
from helpers import print_all_players, print_memories


def main():
    game = Game(10, 5)

    print("=== PLAYERS ===")
    print_all_players(game)

    print("\n=== INITIAL MAP ===")
    game.map.print_map()

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

        # 2. Resolve kills and identify the killer-victim pairs.
        kill_events = game.map.resolve_kills(game.frame)

        # 3. Record observations, excluding the killer's own kill encounter.
        game.record_sightings(kill_events)

        # 4. Remove dead players from the map.
        game.map.rebuild_map_after_kills()

        # 5. Check for body discoveries.
        game.map.check_reports(game)

        # 6. Print the public map.
        game.map.print_map()

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

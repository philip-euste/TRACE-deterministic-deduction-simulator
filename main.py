from class_Game import Game
from helpers import print_all_players
from colors import install_colorama


# ==========================================
# MAIN
# ==========================================

def main():
    # Enable terminal colours before starting the simulation.
    install_colorama()

    game = Game(10, 5, 2)

    print("=== PLAYERS ===")
    print_all_players(game)

    print("\n=== INITIAL MAP ===")
    game.map.print_map()

    # Continue until one side satisfies its victory condition.
    while (
        game.impostors > 0
        and game.impostors < game.crewmates
    ):

        # ==================================
        # MEETING
        # ==================================

        if game.in_meeting:
            print("\n=== MEETING STARTED ===")

            if game.meeting is not None:
                game.meeting.conduct()

            # Clear bodies only after the meeting has concluded.
            game.map.bodies.clear()

            # End the meeting and allow the simulation to resume.
            game.in_meeting = False
            game.meeting = None

            continue

        # ==================================
        # ADVANCE FRAME
        # ==================================

        input("\nPress Enter to advance one frame...")

        game.frame += 1

        print(
            f"\n\n========== FRAME {game.frame} =========="
        )

        # 1. Everyone moves.
        game.map.move_players(game)

        # 2. Resolve kills and identify killer-victim pairs.
        kill_events = game.map.resolve_kills(game.frame)

        # 3. Record observations, excluding killer's own kill encounter.
        game.record_sightings(kill_events)

        # 4. Remove dead players from the map.
        game.map.rebuild_map_after_kills()

        # 5. Check for body discoveries.
        game.map.check_reports(game)

        # 6. Print the public map.
        game.map.print_map()

    # ======================================
    # GAME OVER
    # ======================================

    print("\n" + "=" * 60)
    print("GAME OVER")
    print("=" * 60)

    if game.impostors == 0:
        print("CREWMATES WIN!")

    else:
        print("IMPOSTORS WIN!")

    print(
        f"Living Impostors: {game.impostors}"
    )

    print(
        f"Living Crewmates: {game.crewmates}"
    )

    # ======================================
    # FINAL RESULTS
    # ======================================

    print("\n=== FINAL PLAYERS ===")
    print_all_players(game)

if __name__ == "__main__":
    main()
from helpers import Game, print_all_players


def main():
    game = Game()

    print("=== PLAYERS ===")
    print_all_players(game)

    print("\n=== MAP ===")
    game.map.print_map()



if __name__ == "__main__":
    main()
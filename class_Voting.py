# ==========================================
# VOTING
# ==========================================

class Voting:
    def __init__(self, meeting):
        self.meeting = meeting
        self.game = meeting.game

        # Store each player's votes separately for every body.
        self.player_votes = {
            player: {}
            for player in self.game.players
        }

        # Store the accumulated votes from all bodies.
        self.vote_counts = {
            player: 0
            for player in self.game.players
        }

        self.ejected_player = None

    # ======================================
    # PLAYER VOTE SELECTION
    # ======================================

    def get_player_votes(self, player, body):
        # Dead players cannot vote.
        if not player.alive:
            return []

        possible_killers = (
            self.meeting.get_possible_killers(body)
        )

        candidate_scores = {}

        for candidate in possible_killers:

            # Crewmates cannot vote for themselves.
            if not player.is_impostor and candidate == player:
                continue

            # Impostors cannot vote for another Impostor.
            if (
                player.is_impostor
                and candidate.is_impostor
            ):
                continue

            possible_frames = (
                self.meeting.get_candidate_kill_frames(
                    body,
                    candidate
                )
            )

            candidate_scores[candidate] = len(
                possible_frames
            )

        if not candidate_scores:
            return []

        highest_score = max(
            candidate_scores.values()
        )

        # Vote for every candidate tied at the highest score.
        return [
            candidate
            for candidate, score in candidate_scores.items()
            if score == highest_score
        ]

    # ======================================
    # COLLECT VOTES
    # ======================================

    def collect_votes(self):
        # Calculate votes separately for every body.
        print("\n" + "=" * 60)
        print("INDIVIDUAL VOTING")
        print("=" * 60)

        if not self.meeting.bodies:
            print("No bodies to vote on.")
            return

        for body in self.meeting.bodies:
            print(
                f"\n--- VOTES FOR {body.player.name}'S BODY ---"
            )

            for player in self.game.players:
                votes = self.get_player_votes(
                    player,
                    body
                )

                self.player_votes[player][body.player.name] = votes

                if player.alive:
                    # Add this body's votes to the final tally.
                    for candidate in votes:
                        self.vote_counts[candidate] += 1

                    vote_names = [
                        candidate.name
                        for candidate in votes
                    ]

                    print(
                        f"{player.name} voted for "
                        f"{vote_names} "
                        f"for {body.player.name}'s body"
                    )

                else:
                    print(
                        f"{player.name} voted for [] "
                        f"for {body.player.name}'s body "
                        f"(dead)"
                    )

    # ======================================
    # FINAL TALLY
    # ======================================

    def calculate_results(self):
        # Display the accumulated votes from every body.
        print("\n" + "=" * 60)
        print("FINAL VOTE TALLY")
        print("=" * 60)

        for player in self.game.players:
            print(
                f"{player.name}: "
                f"{self.vote_counts[player]} vote(s)"
            )

        living_players = [
            player
            for player in self.game.players
            if player.alive
        ]

        if not living_players:
            print("\nNo living players remain.")
            return None

        highest_votes = max(
            self.vote_counts[player]
            for player in living_players
        )

        # No votes means nobody is ejected.
        if highest_votes == 0:
            print("\nNobody received any votes.")
            print("Nobody is ejected.")
            return None

        highest_candidates = [
            player
            for player in living_players
            if self.vote_counts[player] == highest_votes
        ]

        # A tie means nobody is ejected.
        if len(highest_candidates) > 1:
            tied_names = [
                player.name
                for player in highest_candidates
            ]

            print(
                f"\nTie between: {tied_names}"
            )

            print("Nobody is ejected.")

            return None

        return highest_candidates[0]

    # ======================================
    # EJECTION
    # ======================================

    def resolve_ejection(self):
        # Eject the player with the highest unique vote count.
        ejected_player = self.calculate_results()

        if ejected_player is None:
            return None

        ejected_player.alive = False

        self.ejected_player = ejected_player

        # Remove the ejected player from map occupancy.
        self.game.map.rebuild_map(self.game)

        print(
            f"\n{ejected_player.name} was ejected!"
        )

        return ejected_player

    # ======================================
    # VOTING EXECUTION
    # ======================================

    def conduct(self):
        self.collect_votes()
        return self.resolve_ejection()
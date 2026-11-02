from class_Voting import Voting


# ==========================================
# MEETING
# ==========================================

class Meeting:
    def __init__(self, game, reporter):
        self.game = game
        self.reporter = reporter

        # Every dead player is investigated.
        self.bodies = game.map.bodies.copy()

        self.shared_sightings = []
        self.shared_positions = {}
        self.statements = []

    # ======================================
    # AUTOMATIC DISCLOSURE
    # ======================================

    def share_position(self, player):
        # Disclose the player's current meeting position.
        if not player.alive or player.position is None:
            return False

        self.shared_positions[player.name] = player.position

        self.statements.append({
            "speaker": player.name,
            "type": "position",
            "cell": player.position
        })

        return True

    def is_concealed_kill_sighting(self, player, sighting):
        # An Impostor omits sightings of players they killed.
        if not player.is_impostor:
            return False

        return any(
            body.killer == player
            and body.player.name == sighting["player"]
            for body in self.game.map.bodies
        )

    def share_sighting(self, player, sighting_index):
        # Disclose one observation from private memory.
        if not player.alive:
            return False

        if not 0 <= sighting_index < len(
            player.memory["sightings"]
        ):
            return False

        original = player.memory["sightings"][sighting_index]

        # Conceal encounters with the Impostor's own victims.
        if self.is_concealed_kill_sighting(player, original):
            return False

        observation = {
            "observer": player.name,
            "player": original["player"],
            "frame": original["frame"],
            "cell": original["cell"]
        }

        key = (
            observation["observer"],
            observation["player"],
            observation["frame"],
            observation["cell"]
        )

        for existing in self.shared_sightings:
            existing_key = (
                existing["observer"],
                existing["player"],
                existing["frame"],
                existing["cell"]
            )

            if key == existing_key:
                return False

        self.shared_sightings.append(observation)

        self.statements.append({
            "speaker": player.name,
            "type": "sighting",
            "observation": observation.copy()
        })

        return True

    def share_all_sightings(self, player):
        count = 0

        for index in range(len(player.memory["sightings"])):
            if self.share_sighting(player, index):
                count += 1

        return count

    def disclose_all_information(self):
        # Every living player shares their position and eligible sightings.
        print("\n=== AUTOMATIC INFORMATION DISCLOSURE ===")

        for player in self.game.players:
            if not player.alive:
                continue

            self.share_position(player)

            count = self.share_all_sightings(player)

            print(
                f"{player.name}: "
                f"Position {player.position} | "
                f"{count} sighting(s) disclosed."
            )

    # ======================================
    # EVIDENCE VERIFICATION
    # ======================================

    def verify_shared_sightings(self):
        for evidence in self.shared_sightings:
            observer = next(
                (
                    player
                    for player in self.game.players
                    if player.name == evidence["observer"]
                ),
                None
            )

            if observer is None:
                return False

            original_exists = any(
                sighting["player"] == evidence["player"]
                and sighting["frame"] == evidence["frame"]
                and sighting["cell"] == evidence["cell"]
                for sighting in observer.memory["sightings"]
            )

            if not original_exists:
                return False

        return True

    def verify_shared_positions(self):
        for player in self.game.players:
            if not player.alive:
                continue

            if player.name not in self.shared_positions:
                return False

            if self.shared_positions[player.name] != player.position:
                return False

        return True

    # ======================================
    # MOVEMENT CONSTRAINTS
    # ======================================

    def get_player_constraints(self, player_name):
        # Build confirmed position constraints from shared observations.
        constraints = {}

        def add_constraint(frame, cell):
            if frame not in constraints:
                constraints[frame] = {cell}
            else:
                constraints[frame].intersection_update({cell})

        for evidence in self.shared_sightings:

            # The target's position is confirmed.
            if evidence["player"] == player_name:
                add_constraint(
                    evidence["frame"],
                    evidence["cell"]
                )

            # The observer was in the same cell.
            if evidence["observer"] == player_name:
                add_constraint(
                    evidence["frame"],
                    evidence["cell"]
                )

        # Meeting position is a final position constraint.
        if player_name in self.shared_positions:
            add_constraint(
                self.game.frame,
                self.shared_positions[player_name]
            )

        return constraints

    # ======================================
    # FORWARD REACHABILITY
    # ======================================

    def get_forward_reachable(self, player_name, max_frame):
        # Calculate every position consistent with observations and movement.
        constraints = self.get_player_constraints(player_name)

        all_cells = {
            (x, y)
            for x in range(self.game.map.length)
            for y in range(self.game.map.length)
        }

        # Frame 0 has an unknown spawn location.
        reachable = {
            0: all_cells.copy()
        }

        if 0 in constraints:
            reachable[0].intersection_update(constraints[0])

        for frame in range(1, max_frame + 1):
            next_positions = set()

            for previous_position in reachable[frame - 1]:
                # Includes staying still and all valid orthogonal moves.
                possible_moves = self.game.map.get_neighbors(
                    previous_position
                )

                next_positions.update(possible_moves)

            # Remove positions contradicting observations.
            if frame in constraints:
                next_positions.intersection_update(
                    constraints[frame]
                )

            reachable[frame] = next_positions

        return reachable

    # ======================================
    # BACKWARD REACHABILITY
    # ======================================

    def get_feasible_trajectory(self, player_name):
        # Combine past reachability with the known meeting position.
        meeting_frame = self.game.frame

        forward = self.get_forward_reachable(
            player_name,
            meeting_frame
        )

        feasible = {
            meeting_frame: forward[meeting_frame].copy()
        }

        for frame in range(meeting_frame - 1, -1, -1):
            possible_previous = set()

            for previous_position in forward[frame]:
                # Staying still is also a valid transition.
                possible_moves = self.game.map.get_neighbors(
                    previous_position
                )

                if any(
                    neighbor in feasible[frame + 1]
                    for neighbor in possible_moves
                ):
                    possible_previous.add(previous_position)

            feasible[frame] = possible_previous

        return feasible

    # ======================================
    # VICTIM REACHABILITY
    # ======================================

    def get_victim_reachability(self, body):
        # Calculate where the victim could have been before discovery.
        tod_range = self.get_tod_range(body)

        return self.get_forward_reachable(
            body.player.name,
            tod_range["latest"]
        )

    def get_possible_death_frames(self, body):
        # Find death frames consistent with the time and victim movement.
        tod_range = self.get_tod_range(body)

        earliest = tod_range["earliest"]

        if earliest is None:
            earliest = 1

        latest = tod_range["latest"]

        victim_reachability = self.get_victim_reachability(
            body
        )

        possible_frames = []

        for frame in range(earliest, latest + 1):
            reachable_positions = victim_reachability[frame]

            if body.discovered:
                # The victim must be able to reach the known body location.
                if body.position in reachable_positions:
                    possible_frames.append(frame)

            else:
                # The victim must have at least one possible death position.
                if reachable_positions:
                    possible_frames.append(frame)

        return possible_frames

    # ======================================
    # TIME OF DEATH
    # ======================================

    def get_tod_range(self, body):
        # Sightings happen before kill resolution, so death can occur
        # during the same frame as the victim's last sighting.
        latest = (
            body.discovery_frame
            if body.discovered
            else self.game.frame
        )

        last_seen_frames = [
            evidence["frame"]
            for evidence in self.shared_sightings
            if evidence["player"] == body.player.name
            and evidence["frame"] <= latest
        ]

        if not last_seen_frames:
            return {
                "earliest": None,
                "latest": latest
            }

        return {
            "earliest": max(last_seen_frames),
            "latest": latest
        }

    # ======================================
    # BODY LOCATION DEDUCTION
    # ======================================

    def get_possible_locations_by_frame(self, body):
        # Calculate possible body locations for every possible death frame.
        possible_frames = self.get_possible_death_frames(body)

        victim_reachability = self.get_victim_reachability(
            body
        )

        if body.discovered:
            return {
                frame: {body.position}
                for frame in possible_frames
            }

        # A living player standing on an undiscovered body would normally
        # have reported it. The killer is exempt only during the death frame.
        occupied_cells = set()

        for player in self.game.players:
            if not player.alive or player.position is None:
                continue

            if (
                player == body.killer
                and self.game.frame == body.death_frame
            ):
                continue

            occupied_cells.add(player.position)

        locations_by_frame = {}

        for frame in possible_frames:
            possible_cells = (
                victim_reachability[frame].copy()
            )

            possible_cells.difference_update(
                occupied_cells
            )

            locations_by_frame[frame] = possible_cells

        return locations_by_frame

    def get_possible_locations(self, body):
        # Combine possible locations across all possible death frames.
        if body.discovered:
            return [body.position]

        locations_by_frame = (
            self.get_possible_locations_by_frame(body)
        )

        possible_locations = set()

        for locations in locations_by_frame.values():
            possible_locations.update(locations)

        return sorted(possible_locations)

    # ======================================
    # KILLER DEDUCTION
    # ======================================

    def get_candidate_kill_frames(self, body, candidate):
        # A candidate must be physically capable of sharing the victim's cell.
        # Their own testimony is not required because an Impostor may omit it.
        if not self.verify_shared_sightings():
            raise ValueError("Sighting verification failed.")

        if not self.verify_shared_positions():
            raise ValueError("Position verification failed.")

        candidate_trajectory = (
            self.get_feasible_trajectory(candidate.name)
        )

        locations_by_frame = (
            self.get_possible_locations_by_frame(body)
        )

        possible_kill_frames = []

        for frame, victim_locations in locations_by_frame.items():

            # A reporter cannot have killed this victim during the
            # same frame in which they reported the body.
            if (
                candidate == body.reported_by
                and frame == body.discovery_frame
            ):
                continue

            candidate_positions = candidate_trajectory[frame]

            shared_locations = (
                victim_locations.intersection(candidate_positions)
            )

            if shared_locations:
                possible_kill_frames.append(frame)

        return possible_kill_frames

    def get_possible_killers(self, body):
        # Return living players who could have shared the victim's cell.
        candidates = [
            player
            for player in self.game.players
            if player.alive and player != body.player
        ]

        remaining_candidates = []

        for candidate in candidates:
            possible_frames = self.get_candidate_kill_frames(
                body,
                candidate
            )

            if possible_frames:
                remaining_candidates.append(candidate)

        return remaining_candidates

    def get_deduction_result(self, body):
        # Summarize the current investigation.
        tod_range = self.get_tod_range(body)

        possible_frames = self.get_possible_death_frames(
            body
        )

        locations = self.get_possible_locations(body)

        candidates = self.get_possible_killers(body)

        if len(candidates) == 1:
            status = "unique"

        elif len(candidates) == 0:
            status = "inconsistent"

        else:
            status = "ambiguous"

        return {
            "status": status,
            "tod_range": tod_range,
            "possible_frames": possible_frames,
            "locations": locations,
            "candidates": candidates
        }

    # ======================================
    # DISPLAY
    # ======================================

    def print_positions(self):
        # Display disclosed meeting positions.
        print("\n=== DISCLOSED MEETING POSITIONS ===")

        for name, position in self.shared_positions.items():
            print(f"{name}: {position}")

    def print_evidence(self):
        # Display every sighting shared during the meeting.
        print("\n=== SHARED SIGHTINGS ===")

        if not self.shared_sightings:
            print("No observations have been shared.")
            return

        for index, evidence in enumerate(
            self.shared_sightings,
            start=1
        ):
            print(
                f"{index}. {evidence['observer']} reports: "
                f"Saw {evidence['player']} "
                f"at {evidence['cell']} "
                f"during frame {evidence['frame']}."
            )

    def print_trajectory(self, player):
        # Display a living player's feasible positions across all frames.
        trajectory = self.get_feasible_trajectory(
            player.name
        )

        print(f"\n=== {player.name}'S FEASIBLE TRAJECTORY ===")

        for frame in range(self.game.frame + 1):
            positions = sorted(trajectory[frame])

            print(
                f"Frame {frame}: {positions}"
            )

    def print_body_investigation(self, body):
        # Display the evidence and deduction result for one body.
        print("\n" + "-" * 60)

        print(f"VICTIM: {body.player.name}")
        print("Status: DEAD")

        if body.discovered:
            print(f"Body location: {body.position}")
            print(f"Discovery frame: {body.discovery_frame}")

        else:
            print("Body location: UNKNOWN")

            locations = self.get_possible_locations(body)

            print("Possible locations:")

            if locations:
                for location in locations:
                    print(f"- {location}")
            else:
                print("No possible locations. Evidence conflicts.")

        result = self.get_deduction_result(body)

        tod_range = result["tod_range"]

        print("\nTIME OF DEATH")

        if tod_range["earliest"] is None:
            print(
                f"Frame 1 to Frame {tod_range['latest']}."
            )
        else:
            print(
                f"Frame {tod_range['earliest']} "
                f"to Frame {tod_range['latest']}."
            )

        print(
            f"Feasible death frames: "
            f"{result['possible_frames']}"
        )

        print("\nPOSSIBLE KILLERS")

        if result["status"] == "unique":
            print(
                f"Unique candidate: "
                f"{result['candidates'][0].name}"
            )

        elif result["status"] == "ambiguous":
            for candidate in result["candidates"]:
                frames = self.get_candidate_kill_frames(
                    body,
                    candidate
                )

                print(
                    f"- {candidate.name} "
                    f"(possible death frames: {frames})"
                )

        else:
            print("No candidate satisfies the evidence.")

    def print_investigation(self):
        # Investigate every body, including undiscovered bodies.
        print("\n" + "=" * 60)
        print("MULTI-BODY INVESTIGATION")
        print("=" * 60)

        print(f"Total deaths: {len(self.bodies)}")

        for body in self.bodies:
            self.print_body_investigation(body)

        print("\n" + "=" * 60)

    # ======================================
    # MEETING EXECUTION
    # ======================================

    def conduct(self):
        # Run disclosure, verification, investigation, and voting.
        print("\n" + "=" * 60)
        print("MEETING")
        print("=" * 60)

        print(f"Reported by: {self.reporter.name}")

        self.disclose_all_information()

        print("\n=== VERIFYING EVIDENCE ===")

        if not self.verify_shared_sightings():
            print("Sighting verification failed.")
            return

        if not self.verify_shared_positions():
            print("Position verification failed.")
            return

        print("All shared evidence is verified.")

        self.print_positions()
        self.print_evidence()

        # Display trajectories of living players.
        for player in self.game.players:
            if player.alive:
                self.print_trajectory(player)

        self.print_investigation()

        # Begin voting after all bodies have been investigated.
        voting = Voting(self)
        voting.conduct()
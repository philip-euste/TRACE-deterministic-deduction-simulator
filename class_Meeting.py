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
        self.shared_alibis = []

        self.statements = []

        # Store alibis separately for each body and candidate.
        self.alibi_disclosures = {}

        # Preserve the original candidate-frame requirements.
        self.initial_alibi_requirements = {}

    # ======================================
    # SIGHTING DISCLOSURE
    # ======================================

    def is_concealed_kill_sighting(self, player, sighting):
        # An Impostor omits sightings of players they killed.
        if not player.is_impostor:
            return False

        return any(
            body.killer == player
            and body.player.name == sighting["player"]
            for body in self.bodies
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
        # Every living player shares eligible sightings.
        print("\n=== AUTOMATIC INFORMATION DISCLOSURE ===")

        for player in self.game.players:
            if not player.alive:
                continue

            count = self.share_all_sightings(player)

            print(
                f"{player.name}: "
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

    # ======================================
    # EXPLICIT ALIBIS
    # ======================================

    def get_initial_candidate_kill_frames(
        self,
        body,
        candidate
    ):
        # Calculate possible kill frames without explicit alibis.
        if not self.verify_shared_sightings():
            raise ValueError("Sighting verification failed.")

        candidate_trajectory = (
            self.get_feasible_trajectory(
                candidate.name,
                include_alibis=False
            )
        )

        locations_by_frame = (
            self.get_possible_locations_by_frame(
                body,
                include_alibis=False
            )
        )

        possible_kill_frames = []

        for frame, victim_locations in locations_by_frame.items():

            # A reporter cannot kill during their reporting frame.
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

    def prepare_alibi_requirements(self):
        # Calculate every requirement before anyone discloses an alibi.
        self.initial_alibi_requirements = {}

        for body in self.bodies:
            candidates = [
                player
                for player in self.game.players
                if player.alive and player != body.player
            ]

            for candidate in candidates:
                frames = self.get_initial_candidate_kill_frames(
                    body,
                    candidate
                )

                self.initial_alibi_requirements[
                    (body, candidate)
                ] = frames

    def share_candidate_alibi(
        self,
        body,
        candidate,
        frame
    ):
        # Disclose a candidate's actual position at one frame.
        if not candidate.alive:
            return False

        position = candidate.position_history.get(frame)

        if position is None:
            return False

        key = (body, candidate)

        if key not in self.alibi_disclosures:
            self.alibi_disclosures[key] = {}

        # Avoid duplicate disclosures.
        if frame in self.alibi_disclosures[key]:
            return False

        disclosure = {
            "body": body.player.name,
            "candidate": candidate.name,
            "frame": frame,
            "position": position
        }

        self.alibi_disclosures[key][frame] = disclosure

        self.shared_alibis.append(disclosure)

        self.statements.append({
            "speaker": candidate.name,
            "type": "alibi",
            "disclosure": disclosure.copy()
        })

        return True

    def disclose_all_alibis(self):
        # Explicit mode requires every candidate to disclose
        # every frame in their initial possible kill-frame list.
        if self.game.alibi_mode != 1:
            return

        print("\n=== EXPLICIT ALIBI DISCLOSURE ===")

        # First calculate all requirements using the original evidence.
        self.prepare_alibi_requirements()

        # Then collect the required disclosures.
        for body in self.bodies:
            print(
                f"\n--- ALIBIS FOR {body.player.name}'S BODY ---"
            )

            candidates = [
                player
                for player in self.game.players
                if player.alive and player != body.player
            ]

            for candidate in candidates:
                frames = self.initial_alibi_requirements.get(
                    (body, candidate),
                    []
                )

                if not frames:
                    continue

                print(
                    f"\n{candidate.name} must disclose "
                    f"frames {frames}:"
                )

                for frame in frames:
                    disclosed = self.share_candidate_alibi(
                        body,
                        candidate,
                        frame
                    )

                    if not disclosed:
                        print(
                            f"  Frame {frame}: "
                            "Position unavailable."
                        )
                        continue

                    position = (
                        self.alibi_disclosures[
                            (body, candidate)
                        ][frame]["position"]
                    )

                    print(
                        f"  Frame {frame}: {position}"
                    )

    def verify_shared_alibis(self):
        # Verify every disclosed position against actual history.
        for disclosure in self.shared_alibis:
            candidate = next(
                (
                    player
                    for player in self.game.players
                    if player.name == disclosure["candidate"]
                ),
                None
            )

            if candidate is None:
                return False

            original_position = (
                candidate.position_history.get(
                    disclosure["frame"]
                )
            )

            if original_position != disclosure["position"]:
                return False

        # Verify that every required frame was disclosed.
        if self.game.alibi_mode == 1:
            for key, required_frames in (
                self.initial_alibi_requirements.items()
            ):
                disclosures = self.alibi_disclosures.get(
                    key,
                    {}
                )

                for frame in required_frames:
                    if frame not in disclosures:
                        return False

        return True

    # ======================================
    # MOVEMENT CONSTRAINTS
    # ======================================

    def get_player_constraints(
        self,
        player_name,
        include_alibis=True
    ):
        # Build confirmed position constraints.
        constraints = {}

        def add_constraint(frame, cell):
            if frame not in constraints:
                constraints[frame] = {cell}
            else:
                constraints[frame].intersection_update({cell})

        # Add constraints from shared sightings.
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

        # Add explicitly disclosed positions.
        if (
            include_alibis
            and self.game.alibi_mode == 1
        ):
            for disclosure in self.shared_alibis:
                if disclosure["candidate"] == player_name:
                    add_constraint(
                        disclosure["frame"],
                        disclosure["position"]
                    )

        # Meeting positions are not automatically disclosed.
        return constraints

    # ======================================
    # FORWARD REACHABILITY
    # ======================================

    def get_forward_reachable(
        self,
        player_name,
        max_frame,
        include_alibis=True
    ):
        # Calculate every position consistent with observations.
        constraints = self.get_player_constraints(
            player_name,
            include_alibis
        )

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

            # Remove positions contradicting observations and alibis.
            if frame in constraints:
                next_positions.intersection_update(
                    constraints[frame]
                )

            reachable[frame] = next_positions

        return reachable

    # ======================================
    # BACKWARD REACHABILITY
    # ======================================

    def get_feasible_trajectory(
        self,
        player_name,
        include_alibis=True
    ):
        # Calculate positions consistent with all available constraints.
        meeting_frame = self.game.frame

        forward = self.get_forward_reachable(
            player_name,
            meeting_frame,
            include_alibis
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

    def get_victim_reachability(
        self,
        body,
        include_alibis=True
    ):
        # Calculate where the victim could have been before discovery.
        tod_range = self.get_tod_range(body)

        return self.get_forward_reachable(
            body.player.name,
            tod_range["latest"],
            include_alibis
        )

    def get_possible_death_frames(
        self,
        body,
        include_alibis=True
    ):
        # Find death frames consistent with victim movement.
        tod_range = self.get_tod_range(body)

        earliest = tod_range["earliest"]

        if earliest is None:
            earliest = 1

        latest = tod_range["latest"]

        victim_reachability = self.get_victim_reachability(
            body,
            include_alibis
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

    def get_possible_locations_by_frame(
        self,
        body,
        include_alibis=True
    ):
        # Calculate possible body locations for every possible death frame.
        possible_frames = self.get_possible_death_frames(
            body,
            include_alibis
        )

        victim_reachability = self.get_victim_reachability(
            body,
            include_alibis
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

    def get_possible_locations(
        self,
        body,
        include_alibis=True
    ):
        # Combine possible locations across all possible death frames.
        if body.discovered:
            return [body.position]

        locations_by_frame = (
            self.get_possible_locations_by_frame(
                body,
                include_alibis
            )
        )

        possible_locations = set()

        for locations in locations_by_frame.values():
            possible_locations.update(locations)

        return sorted(possible_locations)

    # ======================================
    # KILLER DEDUCTION
    # ======================================

    def get_candidate_kill_frames(self, body, candidate):
        # Use recalculated trajectories, including explicit alibis.
        if not self.verify_shared_sightings():
            raise ValueError("Sighting verification failed.")

        if (
            self.game.alibi_mode == 1
            and not self.verify_shared_alibis()
        ):
            raise ValueError("Alibi verification failed.")

        candidate_trajectory = (
            self.get_feasible_trajectory(candidate.name)
        )

        locations_by_frame = (
            self.get_possible_locations_by_frame(body)
        )

        possible_kill_frames = []

        for frame, victim_locations in locations_by_frame.items():

            # A reporter cannot have killed this victim during
            # the same frame in which they reported the body.
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
        # Display positions consistent with all disclosed information.
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
            candidate = result["candidates"][0]

            frames = self.get_candidate_kill_frames(
                body,
                candidate
            )

            print(
                f"- {candidate.name} "
                f"(possible death frames: {frames})"
            )

            print("Unique candidate.")

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

        print("\n=== VERIFYING SIGHTINGS ===")

        if not self.verify_shared_sightings():
            print("Sighting verification failed.")
            return

        print("All shared sightings are verified.")

        self.print_evidence()

        # Collect explicit alibis before recalculating trajectories.
        if self.game.alibi_mode == 1:
            self.disclose_all_alibis()

            print("\n=== VERIFYING EXPLICIT ALIBIS ===")

            if not self.verify_shared_alibis():
                print("Alibi verification failed.")
                return

            print("All required alibis are verified.")

        # All trajectories now include every disclosed alibi.
        print("\n=== RECALCULATED FEASIBLE TRAJECTORIES ===")

        for player in self.game.players:
            if player.alive:
                self.print_trajectory(player)

        self.print_investigation()

        # Begin voting after all bodies have been investigated.
        voting = Voting(self)
        voting.conduct()
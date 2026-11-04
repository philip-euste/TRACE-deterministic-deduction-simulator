# TRACE: Deterministic Deduction Simulator

A Python-based multi-agent simulation and deterministic deduction engine inspired by social deduction games. TRACE simulates player movement, encounters, eliminations, sightings, and body discoveries, then reconstructs possible events using **temporal constraints, player trajectories, evidence, and alibi verification**.

The system supports two investigation modes: **Unconfirmed Alibis**, which relies on sightings and movement constraints, and **Explicit Alibis**, which introduces confirmed player positions at relevant frames. Both modes use deterministic reasoning rather than probability-based suspicion scores.

---

## Version

**Development Version**

---

## Features

- Simulate configurable multiplayer deduction games.
- Generate players and randomly assign Impostors.
- Simulate simultaneous player movement across a grid-based map.
- Support staying in place and moving to orthogonally adjacent cells.
- Resolve kills based on player occupancy and Impostor-to-Crewmate ratios.
- Record player sightings with:
  - Observed player.
  - Frame number.
  - Position.
- Maintain player position histories.
- Track eliminated players and discovered bodies.
- Store body information, including:
  - Victim.
  - Death frame.
  - Body position.
  - Killer.
  - Discovery frame.
  - Reporter.
- Enforce body-reporting restrictions.
- Conduct meetings when bodies are discovered.
- Share individual sightings or all available information.
- Verify shared sightings against recorded evidence.
- Calculate forward and backward player reachability.
- Reconstruct feasible player trajectories.
- Calculate possible death frames.
- Determine possible body locations.
- Identify possible killers using movement and evidence constraints.
- Support two investigation modes:
  - Unconfirmed Alibis.
  - Explicit Alibis.
- Collect and verify explicit alibi disclosures.
- Recalculate player trajectories using confirmed alibis.
- Investigate multiple bodies during the same meeting.
- Calculate candidate-based voting results.
- Support tied votes and ejection resolution.
- Reveal the ejected player's actual role.
- Use Colorama for terminal output.

---

## Project Structure

```text
TRACE-deterministic-deduction-simulator/
├── main.py
├── colors.py
├── helpers.py
├── class_Game.py
├── class_Player.py
├── class_Map.py
├── class_Body.py
├── class_Meeting.py
└── class_Voting.py
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Simulation entry point and game loop |
| `colors.py` | Terminal color definitions |
| `helpers.py` | Shared utility functions |
| `class_Game.py` | Game initialization, player management, and evidence recording |
| `class_Player.py` | Player state, role, position, and memory |
| `class_Map.py` | Grid map, movement, kill resolution, and body discovery |
| `class_Body.py` | Body information and discovery state |
| `class_Meeting.py` | Evidence sharing, alibi verification, and deduction |
| `class_Voting.py` | Candidate selection, voting, and ejection |

---

## Explanation

TRACE processes a game through several interconnected stages:

1. **Initialization** — Create players, assign roles, initialize the map, and establish starting positions.
2. **Simulation** — Move players, resolve encounters, process eliminations, and record sightings.
3. **Body Discovery** — Determine whether a player can discover and report a body.
4. **Evidence Collection** — Share sightings and collect additional investigation information.
5. **Trajectory Reconstruction** — Calculate feasible positions using movement and temporal constraints.
6. **Deduction** — Determine possible death frames, body locations, and potential killers.
7. **Voting** — Select candidates based on the available deduction results and resolve ejections.

The general simulation pipeline is:

```text
Game Initialization
        ↓
Player Movement
        ↓
Kill Resolution
        ↓
Sightings Recording
        ↓
Body Discovery
        ↓
Meeting
        ↓
Evidence Collection
        ↓
Trajectory Reconstruction
        ↓
Killer Deduction
        ↓
Voting
        ↓
Ejection Resolution
        ↓
Next Simulation Frame
```

---

### Game Simulation

The simulation operates on a grid-based map.

Each player has:

```text
Name
Role
Alive Status
Current Position
Memory
Position History
```

Players can remain in their current cell or move to an orthogonally adjacent cell.

Movement is resolved simultaneously. The simulation determines the movement of all players before applying their new positions.

This prevents the movement order of individual players from affecting the resulting frame.

### Kill Resolution

Kill resolution is based on the number of Impostors and Crewmates occupying the same cell.

A kill occurs when:

```text
Impostor Count >= Crewmate Count
```

All Crewmates in that cell are eliminated.

The simulation records the resulting kill events and creates body records containing the victim, death frame, position, and killer.

### Sightings

Players record other players occupying the same cell.

Each sighting stores:

```text
Player
Frame
Cell
```

Sightings become evidence during meetings.

The simulation also accounts for the exact kill encounter so that the killer does not automatically record the same encounter as an ordinary sighting of their victim.

### Body Discovery

Bodies can be discovered when an eligible living player occupies the body's location.

A special reporting restriction applies to the killer:

- The killer cannot report their own victim while continuously remaining at the death location.
- The killer becomes eligible to report that body after leaving the location and subsequently returning.
- Other eligible players can report bodies without this restriction.

A discovered body triggers a meeting.

---

## Investigation System

The investigation system is the central component of TRACE.

Rather than assigning arbitrary suspicion scores, the system uses movement constraints and recorded evidence to determine which events remain possible.

### Forward Reachability

Forward reachability calculates every position a player could occupy after a given number of frames.

For example:

```text
Frame 5:
Observed Position = (1, 1)

Frame 6:
Possible Positions = [(1, 1), (1, 2), (2, 1)]

Frame 7:
Possible Positions = [...]
```

The calculation follows the movement rules of the simulation.

### Backward Reachability

Backward reachability works in the opposite direction.

Given a known position at a later frame, the system determines which earlier positions could have led to it.

Combining forward and backward reachability helps eliminate impossible trajectories.

### Feasible Trajectories

A feasible trajectory is a sequence of positions consistent with the available movement rules and evidence.

The system uses recorded sightings and other investigation constraints to narrow the possible positions of each player.

### Possible Death Frames

The system determines which frames could have contained a victim's elimination.

For each possible death frame, the victim must have been capable of reaching a valid death location.

### Possible Body Locations

For discovered bodies, the actual body location is available as investigation evidence.

For undiscovered bodies, the system calculates possible locations from the victim's feasible positions and available information.

### Possible Killers

A player is considered a possible killer when their feasible trajectory and the victim's possible death circumstances do not rule them out.

The resulting candidates are determined by logical constraints rather than probability.

---

## Alibi Modes

TRACE supports two distinct investigation modes.

The selected mode is configured through the fourth argument of the `Game` constructor.

### Mode 0: Unconfirmed Alibis

```python
game = Game(10, 5, 2, 0)
```

In this mode, players do not disclose their actual positions.

The investigation relies on:

- Recorded sightings.
- Movement rules.
- Forward reachability.
- Backward reachability.
- Feasible trajectories.
- Possible death frames.
- Possible body locations.

Player positions remain uncertain unless established by available evidence.

This mode tests how much can be deduced from incomplete information.

### Mode 1: Explicit Alibis

```python
game = Game(10, 5, 2, 1)
```

In this mode, candidates explicitly disclose their recorded positions at the frames relevant to their initial possible-kill-frame requirements.

For example:

```text
P5:
Frame 10: (1, 2)
Frame 11: (2, 2)
Frame 12: (2, 3)
```

The system verifies these disclosures against recorded position history.

Confirmed alibis become additional constraints for the investigation.

The system then recalculates feasible trajectories and possible killers using the disclosed information.

### Comparison

| Property | Unconfirmed | Explicit |
|---|---|---|
| Sightings | Used | Used |
| Movement constraints | Used | Used |
| Confirmed position disclosures | No | Yes |
| Alibi verification | No | Yes |
| Trajectory recalculation | Yes | Yes |
| Position uncertainty | Higher | Reduced by disclosures |

The two modes allow comparisons between deduction using incomplete observations and deduction with additional confirmed positional evidence.

---

## Voting System

After the investigation, living players vote on possible killers.

The voting system evaluates candidate kill-frame counts.

For each body:

1. Retrieve the possible killer candidates.
2. Calculate the number of possible death frames associated with each candidate.
3. Exclude the voting player from their own Crewmate vote.
4. Prevent Impostors from voting for other Impostors.
5. Select the candidate or candidates with the highest number of possible frames.
6. Accumulate votes across investigated bodies.

Tied candidates can receive votes simultaneously.

### Final Vote Tally

The accumulated votes are evaluated after all bodies have been investigated.

The player with the highest unique vote count is ejected.

If multiple living players share the highest vote count, the result is a tie and nobody is ejected.

The ejected player's actual role is then revealed.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/philip-euste/TRACE-deterministic-deduction-simulator.git

cd TRACE-deterministic-deduction-simulator
```

### Requirements

Python 3.10 or newer.

Install the required package:

```bash
pip install colorama
```

Alternatively, install dependencies from `requirements.txt` if provided.

---

## Configuration

The simulation is initialized through the `Game` class.

```python
game = Game(10, 5, 2, 0)
```

The constructor arguments are:

```text
Game(
    player_count,
    length,
    murderer_count,
    alibi_mode
)
```

| Argument | Description |
|---|---|
| `player_count` | Total number of players |
| `length` | Grid map dimension |
| `murderer_count` | Number of Impostors |
| `alibi_mode` | Investigation mode |

The alibi mode accepts:

```text
0 → Unconfirmed Alibis
1 → Explicit Alibis
```

For example:

```python
game = Game(10, 5, 2, 0)
```

Initializes a 10-player game with a 5 × 5 map, 2 Impostors, and Unconfirmed Alibis.

```python
game = Game(10, 5, 2, 1)
```

Initializes the same game configuration with Explicit Alibis.

---

## Usage

Run the simulation:

```bash
python main.py
```

The program initializes the game and begins the simulation.

During execution, the terminal displays:

- Player movement and map state.
- Kill events.
- Body discoveries.
- Meeting information.
- Shared sightings.
- Alibi disclosures and verification.
- Feasible player trajectories.
- Possible death frames.
- Possible body locations.
- Possible killers.
- Individual votes.
- Final voting results.
- Ejection and role reveal.

---

## Dependencies

- Python 3.10+
- `colorama`
- Python Standard Library:
  - `random`
  - `typing`

---

## Design Philosophy

TRACE is built around deterministic deduction.

The simulation maintains the actual game state, while the investigation system reasons from the information available during a meeting.

These are separate perspectives:

**Simulation State**

Contains the actual positions, roles, eliminations, and events.

**Investigation State**

Contains observations, disclosed information, movement constraints, and possible explanations.

The objective is to reconstruct what could have happened without relying on arbitrary suspicion scores or probabilistic assumptions.

---

## Repository

GitHub: https://github.com/philip-euste/TRACE-deterministic-deduction-simulator

---

## Attribution

TRACE is an independent Python project inspired by social deduction games.

It is not affiliated with or endorsed by InnerSloth or the creators of Among Us.

---

## License

See the `LICENSE` file for licensing information, if included.
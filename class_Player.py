# ==========================================
# PLAYER
# ==========================================

class Player:
    def __init__(self, name):
        self.name = name
        self.is_impostor = False
        self.alive = True
        self.position: tuple[int, int] | None = None

        self.memory = {
            "sightings": []
        }

        # Actual position history, indexed by frame.
        self.position_history = {}

    def __repr__(self):
        return self.name
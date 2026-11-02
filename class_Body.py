# ==========================================
# BODY
# ==========================================

class Body:
    def __init__(self, player, position, death_frame, killer):
        self.player = player

        # Hidden ground truth.
        self.position = position
        self.death_frame = death_frame
        self.killer = killer

        # Public investigation information.
        self.discovery_frame = None
        self.reported_by = None

    @property
    def discovered(self):
        return self.discovery_frame is not None

    def __repr__(self):
        return f"Body({self.player.name})"
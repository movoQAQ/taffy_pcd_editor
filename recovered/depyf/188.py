def _rotate_held_view(self):
    if self.rotate_direction:
        if not self.rotate_clock.isValid():
            return None
    else:
        return None
    seconds = self.rotate_clock.restart() / 1000
    self.rotate_around_z(self.rotate_direction * 10.0 * seconds)
    return None

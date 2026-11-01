def start_held_rotation(self, direction):
    self.rotate_direction = direction
    self.rotate_clock.start()
    self.rotate_timer.start()
    return None

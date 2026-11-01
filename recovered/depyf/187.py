def stop_held_rotation(self):
    self.rotate_timer.stop()
    self.rotate_direction = 0
    return None

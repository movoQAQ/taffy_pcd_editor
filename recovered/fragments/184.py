# Source Generated with Decompyle++
# File: 184.pyc (Python 3.10)

bounds = self.points_actor.GetBounds()
center = (lambda .0 = None: [ (bounds[i] + bounds[i + 1]) * 0.5 for i in .0 ])((0, 2, 4))
radius = max(bounds[1] - bounds[0], bounds[3] - bounds[2]) * 0.5
camera = self.renderer.GetActiveCamera()
# WARNING: Decompyle incomplete

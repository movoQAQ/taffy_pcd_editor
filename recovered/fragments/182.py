# Source Generated with Decompyle++
# File: 182.pyc (Python 3.10)

camera = self.renderer.GetActiveCamera()
bounds = self.points_actor.GetBounds()
center = (lambda .0 = None: [ (bounds[i] + bounds[i + 1]) * 0.5 for i in .0 ])((0, 2, 4))
radius = max(1.0, np.linalg.norm([
    bounds[1] - bounds[0],
    bounds[3] - bounds[2],
    bounds[5] - bounds[4]]) * 0.5)
distance = radius * 2.7
camera.SetViewUp(0, 0, 1)
# WARNING: Decompyle incomplete

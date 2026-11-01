# Source Generated with Decompyle++
# File: 189.pyc (Python 3.10)

camera = self.renderer.GetActiveCamera()
focal = np.asarray(camera.GetFocalPoint(), float, **('dtype',))
position = np.asarray(camera.GetPosition(), float, **('dtype',))
view_up = np.asarray(camera.GetViewUp(), float, **('dtype',))
angle = np.deg2rad(degrees)
rotation = np.array(((np.cos(angle), -np.sin(angle)), (np.sin(angle), np.cos(angle))))
offset = position - focal
offset[:2] = rotation @ offset[:2]
view_up[:2] = rotation @ view_up[:2]
# WARNING: Decompyle incomplete

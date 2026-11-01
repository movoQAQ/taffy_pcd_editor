# Source Generated with Decompyle++
# File: 094.pyc (Python 3.10)

for actor in self.region_marker_actors:
    self.renderer.RemoveActor(actor)
self.region_marker_actors.clear()
if hasattr(self, 'vtk_widget'):
    self.vtk_widget.GetRenderWindow().Render()
    return None

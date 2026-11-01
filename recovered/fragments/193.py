# Source Generated with Decompyle++
# File: 193.pyc (Python 3.10)

self.point_size = float(size)
self.points_actor.GetProperty().SetPointSize(self.point_size)
self.size_text.setText(f'''{size} px''')
self.vtk_widget.GetRenderWindow().Render()

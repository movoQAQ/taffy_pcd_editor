# Source Generated with Decompyle++
# File: 143.pyc (Python 3.10)

render_window = self.vtk_widget.GetRenderWindow()
self.renderer = vtk.vtkRenderer()
self.renderer.SetBackground(0.978, 0.949, 0.975)
self.renderer.SetBackground2(0.948, 0.912, 0.958)
self.renderer.GradientBackgroundOn()
render_window.AddRenderer(self.renderer)
self.interactor = render_window.GetInteractor()
self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
self.interactor.Initialize()
self.points_actor = vtk.vtkActor()
self.mapper = vtk.vtkPolyDataMapper()
self.points_actor.SetMapper(self.mapper)
self.renderer.AddActor(self.points_actor)
self.low_plane = vtk.vtkPlane()
self.high_plane = vtk.vtkPlane()
self.x_low_plane = vtk.vtkPlane()
self.x_high_plane = vtk.vtkPlane()
self.y_low_plane = vtk.vtkPlane()
self.y_high_plane = vtk.vtkPlane()
self.mapper.AddClippingPlane(self.low_plane)
self.mapper.AddClippingPlane(self.high_plane)
self.mapper.AddClippingPlane(self.x_low_plane)
self.mapper.AddClippingPlane(self.x_high_plane)
self.mapper.AddClippingPlane(self.y_low_plane)
self.mapper.AddClippingPlane(self.y_high_plane)
self.mapper.SetScalarModeToUsePointFieldData()
self.mapper.SelectColorArray('Elevation')
self.mapper.SetScalarVisibility(True)
self.lookup = vtk.vtkLookupTable()
self.lookup.SetNumberOfTableValues(256)
self.lookup.Build()
stops = [
    (0.0, (0.13, 0.42, 0.65)),
    (0.28, (0.19, 0.67, 0.65)),
    (0.57, (0.68, 0.76, 0.31)),
    (0.8, (0.93, 0.69, 0.24)),
    (1.0, (0.85, 0.36, 0.24))]
# WARNING: Decompyle incomplete

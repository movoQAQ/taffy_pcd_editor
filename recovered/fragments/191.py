# Source Generated with Decompyle++
# File: 191.pyc (Python 3.10)

self.orthographic = not (self.orthographic)
camera = self.renderer.GetActiveCamera()
if self.orthographic:
    camera.ParallelProjectionOn()
    camera.SetParallelScale(52)
    self.view_label.setText('正交  ·  Z 轴高度着色')
else:
    camera.ParallelProjectionOff()
    self.view_label.setText('俯视  ·  Z 轴高度着色')
self.vtk_widget.GetRenderWindow().Render()

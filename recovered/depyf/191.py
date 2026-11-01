def toggle_projection(self):
    self.orthographic = not self.orthographic
    camera = self.renderer.GetActiveCamera()
    if self.orthographic:
        camera.ParallelProjectionOn()
        camera.SetParallelScale(52)
        self.view_label.setText('正交  ·  Z 轴高度着色')
        self.vtk_widget.GetRenderWindow().Render()
        return None
    else:
        camera.ParallelProjectionOff()
        self.view_label.setText('俯视  ·  Z 轴高度着色')
        self.vtk_widget.GetRenderWindow().Render()
        return None

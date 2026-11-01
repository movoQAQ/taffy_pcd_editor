def set_top_view(self):
    bounds = self.points_actor.GetBounds()
    """original function name <listcomp> is illegal, use a temp name."""
    
    
    def __temp_7551(comp_arg_0):
        nonlocal bounds
        __temp_7552 = []
        for __temp_7553 in comp_arg_0:
            i = __temp_7553
            __temp_7552.append((bounds[i] + bounds[i + 1]) * 0.5)
            continue
        return __temp_7552
    
    
    center = __temp_7551(iter((0, 2, 4)))
    radius = max(bounds[1] - bounds[0], bounds[3] - bounds[2]) * 0.5
    camera = self.renderer.GetActiveCamera()
    camera.SetFocalPoint(*center)
    camera.SetPosition(center[0], center[1], center[2] + max(radius * 2.5, 10))
    camera.SetViewUp(0, 1, 0)
    camera.ParallelProjectionOn()
    camera.SetParallelScale(max(radius * 1.08, 1))
    self.orthographic = True
    self.view_label.setText('俯视  ·  Z 轴高度着色')
    self.renderer.ResetCameraClippingRange()
    self.vtk_widget.GetRenderWindow().Render()
    return None

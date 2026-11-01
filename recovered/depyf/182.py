def reset_camera(self):
    camera = self.renderer.GetActiveCamera()
    bounds = self.points_actor.GetBounds()
    """original function name <listcomp> is illegal, use a temp name."""
    
    
    def __temp_7528(comp_arg_0):
        nonlocal bounds
        __temp_7529 = []
        for __temp_7530 in comp_arg_0:
            i = __temp_7530
            __temp_7529.append((bounds[i] + bounds[i + 1]) * 0.5)
            continue
        return __temp_7529
    
    
    center = __temp_7528(iter((0, 2, 4)))
    radius = max(1.0, np.linalg.norm([bounds[1] - bounds[0], bounds[3] - bounds
        [2], bounds[5] - bounds[4]]) * 0.5)
    distance = radius * 2.7
    camera.SetViewUp(0, 0, 1)
    camera.SetFocalPoint(*center)
    camera.SetPosition(center[0] + distance * 0.75, center[1] - distance * 0.85,
        center[2] + distance * 0.95)
    camera.SetViewAngle(34)
    if self.orthographic:
        camera.ParallelProjectionOn()
        camera.SetParallelScale(radius * 0.95)
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()
        return None
    else:
        camera.ParallelProjectionOff()
        self.renderer.ResetCameraClippingRange()
        self.vtk_widget.GetRenderWindow().Render()
        return None

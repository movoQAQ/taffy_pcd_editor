def export_image(self):
    __temp_7618, __temp_7619 = QFileDialog.getSaveFileName(self, '导出视图截图',
        'pointcloud-view.png', 'PNG 图片 (*.png)')
    path = __temp_7618
    _ = __temp_7619
    if not path:
        return None
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(self.vtk_widget.GetRenderWindow())
    capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff()
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(path)
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    return None

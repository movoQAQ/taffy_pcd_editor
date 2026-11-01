# Source Generated with Decompyle++
# File: 194.pyc (Python 3.10)

(path, _) = QFileDialog.getSaveFileName(self, '导出视图截图', 'pointcloud-view.png', 'PNG 图片 (*.png)')
if not path:
    return None
capture = None.vtkWindowToImageFilter()
capture.SetInput(self.vtk_widget.GetRenderWindow())
capture.SetInputBufferTypeToRGB()
capture.ReadFrontBufferOff()
capture.Update()
writer = vtk.vtkPNGWriter()
writer.SetFileName(path)
writer.SetInputConnection(capture.GetOutputPort())
writer.Write()

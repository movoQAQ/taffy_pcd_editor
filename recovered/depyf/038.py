def winId(self):
    nonlocal __class__
    self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
    return super().winId()

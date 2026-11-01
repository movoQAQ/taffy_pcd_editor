def CloudTaskWorker():
    __module__ = __name__
    __qualname__ = 'CloudTaskWorker'
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    
    
    def __init__(self, operation):
        nonlocal __class__
        super().__init__()
        self.operation = operation
        return None
    
    
    def run(self):
        try:
            self.completed.emit(self.operation())
        finally:
            return None
    
    
    __classcell__ = __class__
    return __class__

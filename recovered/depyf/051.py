def run(self):
    try:
        self.completed.emit(self.operation())
    finally:
        return None

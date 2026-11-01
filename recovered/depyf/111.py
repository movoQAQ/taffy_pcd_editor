def <lambda>(error):
    nonlocal self
    return self.region_pick_status.setText('补全失败：' + str(error))

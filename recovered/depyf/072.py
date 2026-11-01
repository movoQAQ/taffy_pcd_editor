def <lambda>(written):
    nonlocal self
    return self.filter_status.setText('已写入：' + str(Path(written).name))

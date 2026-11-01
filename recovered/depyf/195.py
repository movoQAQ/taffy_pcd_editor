def main():
    app = QApplication(sys.argv)
    app.setApplicationName('taffy-editor')
    app.setApplicationDisplayName('taffy编辑器 ' + str(APP_VERSION))
    app.setDesktopFileName('taffy-editor')
    app.setWindowIcon(QIcon(str(Path(__file__).parent / 'assets' /
        'tafei-pcd-editor.png')))
    app.setFont(QFont('Noto Sans CJK SC', 10))
    app.setStyleSheet(APP_STYLE)
    window = PointCloudWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec_())
    return None

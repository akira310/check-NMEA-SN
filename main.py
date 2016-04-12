#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
import sncheck  # my module


class Logger(object):
    u""" GUIへのログ表示用クラス

    GUIへ標準出力、エラー出力をパイプする
    """

    def __init__(self, editor, out=None, color=None):
        self.editor = editor    # 結果出力用エディタ
        self.out = out       # 標準出力・標準エラーなどの出力オブジェクト
        # 結果出力時の色(Noneが指定されている場合、エディタの現在の色を入れる)
        if not color:
            self.color = editor.textColor()
        else:
            self.color = color

    def write(self, message):
        # カーソルを文末に移動。
        self.editor.moveCursor(QtGui.QTextCursor.End)

        # color変数に値があれば、元カラーを残してからテキストのカラーを
        # 変更する。
        self.editor.setTextColor(self.color)

        # 文末にテキストを追加。
        self.editor.insertPlainText(message)

        # 出力オブジェクトが指定されている場合、そのオブジェクトにmessageを
        # 書き出す。
        if self.out:
            self.out.write(message)


class MyGui(QtGui.QMainWindow):
    u""" GUI用クラス

    ディレクトリの指定や結果出力を行う
    """

    def __init__(self):
        super(MyGui, self).__init__()

        self.__create()

    def closeEvent(self, event):
        u""" closeボタン押下時の処理 """

        sys.stdout = None
        sys.stderr = None

    def __create(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.textEdit.setReadOnly(True)
        self.textEdit.setTextColor(QtGui.QColor("blue"))
        self.textEdit.setText(self.__get_readme())
        self.textEdit.setTextColor(QtGui.QColor("black"))

        sys.stdout = Logger(self.textEdit, sys.stdout)
        sys.stderr = Logger(self.textEdit, sys.stderr, QtGui.QColor(255, 0, 0))

        openFile = QtGui.QAction(
                    QtGui.QApplication.style()
                    .standardIcon(QtGui.QStyle.SP_FileDialogStart),
                    'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open Dir')
        openFile.triggered.connect(self.__open)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.setGeometry(100, 100, 750, 300)
        self.setWindowTitle('File dialog')
        self.show()

    def __open(self):
        path = QtGui.QFileDialog.getExistingDirectory(self, 'Open Dir', '.')
        self.__draw(path)

    def __draw(self, path):
        self.textEdit.clear()
        nmea = sncheck.NMEAData()
        trip = nmea.check(nmea.concat_trip(path))

        for tid, v in trip.items():
            print("==================================================")
            print("trip id: ", tid)
            print("TTFF: {ttff}(sec)  {time}".format(
                ttff=v["ttff"], time=v["ttffnmea"]))
            print("--------------------------------------------------")
            for sn in v["sn"]:
                print(sn)

    def __get_readme(self):
        return \
            "\n==========================================================\n" +\
            " SDカードデータのrootディレクトリを指定してください" +\
            "\n==========================================================\n\n"


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MyGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
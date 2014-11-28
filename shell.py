#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys, os, time, pyinotify
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import Qt
import QTermWidget

def get_contents(filename):
    with file(filename) as f:
        return f.read()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, ttyfile, ttyWinId, shellprocess):
        self.ttyfile = ttyfile
        self.ttyWinId = ttyWinId
        self.shellprocess = shellprocess

    def process_IN_CREATE(self, event):
        if event.pathname.endswith(self.ttyfile):
            print "created:", event.pathname
            tty = get_contents(self.ttyfile)
            print(tty)

            env = QProcessEnvironment.systemEnvironment()
            env.insert("LD_PRELOAD", "./overrideexecve.so")
            env.insert("CQRSH_PTY", tty)

            self.shellprocess.setProcessEnvironment(env)
            self.shellprocess.start('xterm',['-into', self.ttyWinId])

class embterminal(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.terminal = QWidget(self)
        self.shellwidget = QWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.terminal)
        layout.addWidget(self.shellwidget)

    def startterminals(self):
        self.process = QProcess(self)
        self.shellprocess = QProcess(self)
        ttyfile = 'tty-%d.txt' % os.getpid()
	if (os.path.exists(ttyfile)):
            os.remove(ttyfile)
        print(ttyfile)

        wm = pyinotify.WatchManager()
        notifier = pyinotify.ThreadedNotifier(wm, EventHandler(ttyfile, str(self.shellwidget.winId()), self.shellprocess))
        notifier.start()
        wm.add_watch('.', pyinotify.IN_CREATE, rec=True)

        self.process.start('xterm',['-hold', '-into', str(self.terminal.winId()), '-e', './detach', ttyfile])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = embterminal()
    main.show()
    print("showed")
    main.startterminals()
    sys.exit(app.exec_())

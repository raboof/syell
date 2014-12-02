#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys, os, time, pyinotify, signal
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import Qt
import QTermWidget

signal.signal(signal.SIGINT, signal.SIG_DFL)

def get_contents(filename):
    with file(filename) as f:
        return f.read()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, ttyfile, termWidget):
        self.ttyfile = ttyfile
        self.termWidget = termWidget

    def process_IN_CREATE(self, event):
        if event.pathname.endswith(self.ttyfile):
            print "created:", event.pathname
            tty = get_contents(self.ttyfile)
            print(tty)

            env = QProcessEnvironment.systemEnvironment()
            env.insert("LD_PRELOAD", "./overrideexecve.so")
            env.insert("CQRSH_PTY", tty)
            self.termWidget.setEnvironment(env.toStringList())
            self.termWidget.startShellProgram()

class embterminal(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.outputterm = QTermWidget.QTermWidget(0, self)
        self.outputterm.setTerminalFont(QFont('DejaVu Sans Mono', 18))
        self.shellterm = QTermWidget.QTermWidget(0, self)
        self.shellterm.setTerminalFont(QFont('DejaVu Sans', 18))
        layout = QVBoxLayout(self)
        layout.addWidget(self.outputterm)
        layout.addWidget(self.shellterm)

    def startterminals(self):
        self.process = QProcess(self)
        ttyfile = 'tty-%d.txt' % os.getpid()
	if (os.path.exists(ttyfile)):
            os.remove(ttyfile)
        print(ttyfile)

        wm = pyinotify.WatchManager()
        notifier = pyinotify.ThreadedNotifier(wm, EventHandler(ttyfile, self.shellterm))
        notifier.start()
        wm.add_watch('.', pyinotify.IN_CREATE, rec=True)

        self.outputterm.setShellProgram('./detach')
        self.outputterm.setArgs([ttyfile])
        self.outputterm.startShellProgram()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = embterminal()
    main.show()
    print("showed")
    main.startterminals()
    sys.exit(app.exec_())

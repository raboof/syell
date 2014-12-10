#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys, os, time, signal, socket, threading, tempfile
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QTcpServer, QTcpSocket

from PyQt4 import Qt
import QTermWidget

signal.signal(signal.SIGINT, signal.SIG_DFL)

path = os.path.dirname(os.path.realpath(__file__))
tty_device_file = "uninitialized"

def get_contents(filename):
    with file(filename) as f:
        return f.read()

class TtyBroker(QTcpServer):
    def __init__(self):
        super(QTcpServer, self).__init__()
        self.listen()
        self.connect(self, SIGNAL('newConnection()'), self.handle)

    def handle(self):
        socket = self.nextPendingConnection()
        requestheader = socket.read(1)
        # TODO start a new terminal as needed, then wait until it's created
        # and return its tty device file
        response = tty_device_file
        responseheader = chr(len(response))

        socket.write(responseheader)
        socket.write(response)
        socket.close()

    def port(self):
        return self.serverPort()

    def stop(self):
        self.close()

class TargetTerminalWidget(QTermWidget.QTermWidget):
    def __init__(self, parent):
        super(QTermWidget.QTermWidget, self).__init__(0, parent)
        self.parent = parent

        self.setTerminalFont(QFont('DejaVu Sans Mono', 18))

        self.ttyfile = tempfile.NamedTemporaryFile(delete=False).name

        self.wm = QFileSystemWatcher(self)
        self.wm.addPath(self.ttyfile)
        self.wm.connect(self.wm, SIGNAL('fileChanged(QString)'), self.ttyStarted)

        self.setShellProgram(path + '/detach')
        self.setArgs([self.ttyfile])
        self.startShellProgram()

        self.setMonitorActivity(1)
        self.connect(self, SIGNAL('activity()'), self.active)

    def active(self):
        self.setMonitorActivity(1)
        self.parent.requestOutputFocus(self)

    def ttyStarted(self, event):
        global tty_device_file
        self.wm.disconnect(self.wm, SIGNAL('fileChanged(QString)'), self.ttyStarted)

        tty_device_file = get_contents(self.ttyfile)
        os.remove(self.ttyfile)

class ShellTerminalWidget(QTermWidget.QTermWidget):
    def __init__(self, broker_port, parent):
        super(QTermWidget.QTermWidget, self).__init__(0, parent)
        self.parent = parent

        env = QProcessEnvironment.systemEnvironment()
        env.insert("LD_PRELOAD",  path + "/overrideexecve.so")
        env.insert("TTY_BROKER_PORT", str(broker_port))

        self.setTerminalFont(QFont('DejaVu Sans', 18))
        self.setEnvironment(env.toStringList())
        self.startShellProgram()

        self.connect(self, SIGNAL('activity()'), self.active)
        self.setMonitorActivity(1)

    def active(self):
        self.setMonitorActivity(1)
        self.parent.requestShellFocus(self)

class syell(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.waitingfornextshell = True
        self.outputting = False

        self.doneOutputting = False
        self.ttyBroker = TtyBroker()

        self.outputterm = TargetTerminalWidget(self)
        self.shellterm = ShellTerminalWidget(self.ttyBroker.port(), self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.outputterm)
        layout.addWidget(self.shellterm)

    def requestOutputFocus(self, widget):
        if (not self.outputting):
            widget.setFocus()
            self.outputting = True
            self.waitingfornextshell = True

    def requestShellFocus(self, widget):
        if (self.waitingfornextshell):
            self.waitingfornextshell = False
        else:
            self.outputting = False

        widget.setFocus()

    def quit(self):
        self.ttyBroker.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = syell()
    main.show()
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), main.quit)
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), app, SLOT('quit()'))
    sys.exit(app.exec_())

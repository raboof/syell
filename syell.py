#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys, os, time, pyinotify, signal, socket, threading
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import Qt
import QTermWidget

from SocketServer import BaseRequestHandler, TCPServer

signal.signal(signal.SIGINT, signal.SIG_DFL)

# TODO discover a random free port to listen on
broker_port = 12351
tty_device_file = "uninitialized"

def get_contents(filename):
    with file(filename) as f:
        return f.read()

class TtyRequestHandler(BaseRequestHandler):
    def handle(self):
        requestheader = self.request.recv(1)
        # TODO start a new terminal as needed, then wait until it's created
        # and return its tty device file
        response = tty_device_file
        responseheader = chr(len(response))

        self.request.sendall(responseheader)
        self.request.sendall(response)
        self.request.close()

class TtyBroker:
    def __init__(self):
        self.server = TCPServer(('',broker_port), TtyRequestHandler)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.start()

    def stop(self):
        self.server.shutdown()


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, ttyfile):
        self.ttyfile = ttyfile

    def process_IN_CREATE(self, event):
        global tty_device_file

        if event.pathname.endswith(self.ttyfile):
            # TODO pass this to the broker instead of using a global variable
            tty_device_file = get_contents(self.ttyfile)
            os.remove(self.ttyfile)

class TargetTerminalWidget(QTermWidget.QTermWidget):
    def __init__(self, parent):
        super(QTermWidget.QTermWidget, self).__init__(0, parent)

        self.setTerminalFont(QFont('DejaVu Sans Mono', 18))

        ttyfile = 'tty-%d.txt' % os.getpid()
	if (os.path.exists(ttyfile)):
            os.remove(ttyfile)

        wm = pyinotify.WatchManager()
        self.ttyHandler = EventHandler(ttyfile)
        self.notifier = pyinotify.ThreadedNotifier(wm, self.ttyHandler)
        self.notifier.start()
        wm.add_watch('.', pyinotify.IN_CREATE, rec=True)

        self.setShellProgram('./detach')
        self.setArgs([ttyfile])
        self.startShellProgram()

    def stop(self):
        self.notifier.stop()

class ShellTerminalWidget(QTermWidget.QTermWidget):
    def __init__(self, parent):
        super(QTermWidget.QTermWidget, self).__init__(0, parent)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("LD_PRELOAD", "./overrideexecve.so")
        env.insert("TTY_BROKER_PORT", str(broker_port))

        self.setTerminalFont(QFont('DejaVu Sans', 18))
        self.setEnvironment(env.toStringList())
        self.startShellProgram()

class syell(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.ttyBroker = TtyBroker()

        self.outputterm = TargetTerminalWidget(self)
        self.shellterm = ShellTerminalWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.outputterm)
        layout.addWidget(self.shellterm)

    def quit(self):
        self.outputterm.stop()
        self.ttyBroker.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = syell()
    main.show()
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), main.quit)
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), app, SLOT('quit()'))
    sys.exit(app.exec_())

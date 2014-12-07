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

class TtyBroker(BaseRequestHandler):
    def handle(self):
        requestheader = self.request.recv(1)
        response = tty_device_file
        responseheader = chr(len(response))

        self.request.sendall(responseheader)
        self.request.sendall(response)
        self.request.close()

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, ttyfile):
        self.ttyfile = ttyfile

    def startbroker(self, ttydevice):
        # TODO find a proper way to tell the broker which device it should respond with..
        global tty_device_file
        tty_device_file = ttydevice
        
        self.server = TCPServer(('',broker_port), TtyBroker)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.start()

    def process_IN_CREATE(self, event):
        if event.pathname.endswith(self.ttyfile):
            tty = get_contents(self.ttyfile)
            os.remove(self.ttyfile)
            self.startbroker(tty)

    def stop(self):
        self.server.shutdown()

class syell(QWidget):

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

        wm = pyinotify.WatchManager()
        self.ttyHandler = EventHandler(ttyfile)
        self.notifier = pyinotify.ThreadedNotifier(wm, self.ttyHandler)
        self.notifier.start()
        wm.add_watch('.', pyinotify.IN_CREATE, rec=True)

        self.outputterm.setShellProgram('./detach')
        self.outputterm.setArgs([ttyfile])
        self.outputterm.startShellProgram()

        env = QProcessEnvironment.systemEnvironment()
        env.insert("LD_PRELOAD", "./overrideexecve.so")
        env.insert("TTY_BROKER_PORT", str(broker_port))
        self.shellterm.setEnvironment(env.toStringList())
        self.shellterm.startShellProgram()

    def quit(self):
        print('quitting')
        self.ttyHandler.stop()
        self.notifier.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = syell()
    main.show()
    main.startterminals()
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), main.quit)
    main.shellterm.connect(main.shellterm, SIGNAL('finished()'), app, SLOT('quit()'))
    sys.exit(app.exec_())

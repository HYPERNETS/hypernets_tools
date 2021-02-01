#!/usr/bin/python3
# coding: utf-8

# source : https://stackoverflow.com/questions/21811464/how-can-i-embed-a-pyth
# on-interpreter-frame-in-python-using-tkinter

# TODO : Catch ctrl-d signal and destroy widgets

from tkinter import BOTH, END, WORD, N, S, E, W
from tkinter import Tk, Text, Frame

import subprocess
import queue
from threading import Thread
import os


class FrameConsole(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.parent = parent
        self.createWidgets()

        # get the path to the console.py file assuming it is in the same folder
        consolePath = os.path.join(os.path.dirname(__file__),
                                   "console_phystar.py")
        # open the console.py file (replace the path to python with the
        # correct one for your system)
        self.p = subprocess.Popen(["python3.8", consolePath],
                                  stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        # make queues for keeping stdout and stderr whilst it is transferred
        # between threads
        self.outQueue = queue.Queue()
        self.errQueue = queue.Queue()

        # keep track of where any line that is submitted starts
        self.line_start = 0

        # make the enter key call the self.enter function
        self.ttyText.bind("<Return>", self.enter)

        # a daemon to keep track of the threads so they can stop running
        self.alive = True

        # start the functions that get stdout and stderr in separate threads
        Thread(target=self.readFromProccessOut).start()
        Thread(target=self.readFromProccessErr).start()

        # start the write loop in the main thread
        self.writeLoop()

    def destroy(self):
        """This is the function that is automatically called when the widget
        is destroyed."""

        self.alive = False
        # write exit() to the console in order to stop it running
        self.p.stdin.write("exit()\n".encode())
        self.p.stdin.flush()
        # call the destroy methods to properly destroy widgets
        self.ttyText.destroy()
        Frame.destroy(self)

    def enter(self, e):
        "The <Return> key press handler"
        string = self.ttyText.get(1.0, END)[self.line_start:]
        self.line_start += len(string)
        self.p.stdin.write(string.encode())
        self.p.stdin.flush()

    def readFromProccessOut(self):
        "To be executed in a separate thread to make read non-blocking"
        while self.alive:
            data = self.p.stdout.raw.read(1024).decode()
            self.outQueue.put(data)

    def readFromProccessErr(self):
        "To be executed in a separate thread to make read non-blocking"
        while self.alive:
            data = self.p.stderr.raw.read(1024).decode()
            self.errQueue.put(data)

    def writeLoop(self):
        "Used to write data from stdout and stderr to the Text widget"
        # if there is anything to write from stdout or stderr, then write it
        if not self.errQueue.empty():
            self.write(self.errQueue.get())
        if not self.outQueue.empty():
            self.write(self.outQueue.get())

        # run this method again after 10ms
        if self.alive:
            self.after(10, self.writeLoop)

    def write(self, string):
        self.ttyText.insert(END, string)
        self.ttyText.see(END)
        self.line_start += len(string)

    def createWidgets(self):
        self.ttyText = Text(self, wrap=WORD)
        self.ttyText.pack(fill=BOTH, expand=True)


if __name__ == '__main__':
    root = Tk()
    root.title("Console Phystar")
    # root.config(background="red")
    frmConsole = FrameConsole(root)
    frmConsole.grid(sticky=W+E+S+N)
    root.mainloop()

# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 13:41:22 2016

@author: Will
"""

# Kevin:
#   Assume I have: remove pyTables (it's too rigid). Use pickel instead.
#      date (one pickel per day).
#          algorithm
#              pattern fitness (unique id: number generated per day).
#   -> GUI/CLI to load these patterns and view them and show charts.
#   -> Assume function to get the pattern.

import sys
import numpy as np
import string
import taskMgr
import matplotlib
import importlib
#import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from tkinter import *
from importlib import * # allows the user to call reload(...) to realod a module. 
import traceback
import multiprocessing
import re
import pickle
import io

##################### Program state #####################

anim = None
result = None

printQ = multiprocessing.Queue() # DO NOT USE queue.Queue(). It will hate you.
# These queues don't keep growing, they hold only one object at most (I think).
workspaceQ = multiprocessing.Queue() # variables are stored here, all in a single data structure.
importsQ = multiprocessing.Queue() # imports are stored here.
wantsClcQ = multiprocessing.Queue()
commandsEntered = [] # all commands the user inputed.
commandsEnteredIndex = 0

##################### Setting up the UI #####################
root = Tk()
emFig = Figure(figsize=(5, 4), dpi=150)
plotter = emFig.add_subplot(111) # use this to plot stuff.

c = FigureCanvasTkAgg(emFig, master=root)
c.show()
c.get_tk_widget().pack(expand=1)
cmdBox = Entry(root,width=80) # Type command here and hit enter.
cmdBox.pack()

outputBox = Text(root) # Type command here and hit enter.
outputBox.pack()

def refresh():
    c.draw()

def pr(*args): # like the original print, but to the outputbox using a queue.
    s = ''     # can be called from any thread.
    for a in args:
        s = s+str(a)+' ' # OK maybe the O(n^2) str concat, but n (the # of args) should be small.
    #print('putting: ',s)
    printQ.put(s)
    #print('size  : ',printQ.qsize())
    #outputBox.insert(END, '\n')
    #outputBox.insert(END, s)

##################### Testing functions #####################

def testPause():
    import time
    pr("Immediate")
    time.sleep(1)
    pr("After 1 second")
    time.sleep(1)
    pr("After 2 second")
    time.sleep(1)
    pr("And after 3 seconds (done)")


#############################################################

def clc(): # Octave-style clear command line.
    wantsClcQ.put(1)

#def clear(*args): # Octave-style clear.
#    print("clear: ")
#    if len(args)==0:
#        workspace.clear()
#    else:
#        for a in args:
#            workspace.pop(a, "Some default so that there is no error when clearing a non-existant var.") 

def prQempty(): # must be called from the main thread due to tkinter bieng picky.
    #print('size: ',printQ.qsize())
    while not printQ.empty():
        #print('getting: ')
        outputBox.insert(END, '\n')
        outputBox.insert(END, printQ.get()) # get() reduces the queue size by 1.

##################### The main control flow #####################
def cmdBoxKeyPress(event):
    global commandsEnteredIndex
    char = event.char
    nCommand = len(commandsEntered)
    #print("pressed", s, event.char == '\uf700',s == '\uf701', nCommand);
    if char == '\uf700' and commandsEnteredIndex > 0: # up arrow, earlier commands.
        commandsEnteredIndex = commandsEnteredIndex-1
    elif char== '\uf701' and commandsEnteredIndex < nCommand-1: # up arrow, earlier commands.
        commandsEnteredIndex = commandsEnteredIndex+1
    if (char == '\uf700') or (char == '\uf701'):
        cmdBox.delete(0, 'end')
        cmdBox.insert(END, commandsEntered[commandsEnteredIndex])

def getFromQueue():
    workspace = {}
    imports = []
    while not importsQ.empty():
        imports = imports+importsQ.get()
    while not workspaceQ.empty():
        workspace.update(workspaceQ.get())
    return [workspace, imports]
def putInQueue(workspace, imports):
    workspaceQ.put(workspace)
    importsQ.put(imports)

def evalTweak(s, workspace, imports): # evals s but puts variables in workspace, etc.
    # TODO: we can't pickle modules, so instead keep a list of import commands and run them each time.
    if (re.match('\ *import ', s) is not None) or (re.match('\ *from ', s) is not None): # Imports or from statements.
        imports.append(s)
    else:
        # Make every value in workspace accessable:
        #print(workspace)
        for key in workspace:
            #print(key+'= workspace["'+key+'"]')
            exec(key+'= workspace["'+key+'"]') # workspace variables shadow other vars with the same name, as in Octave.
        
        # Run the imports:
        for imp in imports:
            try:
                exec(imp)
            except:
                pass
        exec(s) # The command itself (note the exec, not the eval). At this point all the variable scopes should be correct.
        locVarsAfterExec = locals()
        
        fakeFile = io.BytesIO()
        for key in locVarsAfterExec: # Put the variables back into work-space.
            try: # how to check for pickling. There is
                obj = locVarsAfterExec[key]
                pickle.dump(obj, fakeFile)
                workspace[key] = obj
            except pickle.PicklingError:
                pass
    return [workspace, imports]
    
def everyFrame():
    if anim is not None:
        anim.everyFrame()
        if anim.done:
            state['anim'] = None
    prQempty() # empty the queue.
    while not wantsClcQ.empty():
        wantsClcQ.get()
        outputBox.delete(1.0, 'end')
    root.after(25, everyFrame) # everyFrame is an infinite loop without blocking.

def execCmd(s):
    (workspace, imports) = getFromQueue()
    try:
        (workspace, imports) = evalTweak(s, workspace, imports)
    except: # will be the wrong error once in a super-rare event if another error is caused on another thread.
        ex_type, ex, tb = sys.exc_info()
        pr('ERROR:')
        pr(traceback.extract_tb(tb))
        pr(ex_type)
        pr(ex)
    putInQueue(workspace, imports)

def runCmd(_): # ALL commands pass through here.
    global commandsEnteredIndex
    cmdText = cmdBox.get()
    if cmdText[-1]=='\uf700' or cmdText[-1]=='\uf701':
       cmdText = cmdText[0:-1] # remove the last char.
    commandsEntered.append(cmdText)
    taskMgr.future(execCmd, cmdText) 
    cmdBox.delete(0, 'end')
    commandsEnteredIndex = len(commandsEntered)

everyFrame() # initialize the loop.

##################### Activating the main loop #####################
cmdBox.bind('<Return>', runCmd)
cmdBox.bind("<Key>", cmdBoxKeyPress)
root.mainloop() # We never get past this line, instead callbacks are used.






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


##################### UI/Graphics tools #####################
import string
import matplotlib
#import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from tkinter import *

##################### Computational tools #####################
import random
import numpy as np
import concurrent.futures
from subprocess import call
from imp import reload
import time
import life
from sys import argv
call(["python3","setup.py","build_ext","--inplace"])
life = reload(life) # reload it because we built it, the software will have to be ran twice.
pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
poolKey = 0 # every time a callback starts this goes up by 1.
            # During a callback: Every time we get to a frame, check if poolKey matches what it was at the start of the fn. 
                 # stop if it does not match.

##################### Inputs to script #####################
script,h,w,tmax = argv
h = int(h)
w = int(w)
tmax = int(tmax)


##################### Setting up the UI #####################
root = Tk()
emFig = Figure(figsize=(5, 4), dpi=150)
plotter = emFig.add_subplot(111) # use this to plot stuff.

c = FigureCanvasTkAgg(emFig, master=root)
c.show()
c.get_tk_widget().pack(expand=1)
cmdBox = Entry(root) # Type command here and hit enter.
cmdBox.pack()
def refresh():
    c.draw()

##################### Command functions #####################

# Makes random data for testing the algorythim on:
def randData(x,y):
	out = np.zeros((x,y), np.int)
	for i in range(x):
		for j in range(y):
			out[i,j]= round(random.random()*0.58)
	return out 

def plotTest(args):
    global poolKey
    key0 = poolKey
    # even fns that don't check fo rinterruptions
    # need to set poolStatus at the end.
    
    if len(args)==0:
        args.append(1)
    freq = float(args[0])
    t = np.arange(0.0, 2.0, 0.01)
    s = np.sin(2*np.pi*t*freq)
    plotter.clear()
    plotter.plot(t,s)
    refresh()
    print("plotted")
    poolStatus = 'open'   

def plotTestAnim(_):
    global poolKey
    key0 = poolKey
    
    print('plot anim start')
    for i in range(0,50):
        t = np.arange(0.0, 2.0, 0.01)
        s = np.sin(2*np.pi*t*0.1*i)
        plotter.clear()
        plotter.plot(t,s)
        print('plot anim ',i)
        if poolKey is not key0:
            print('plot anim INTERRUPT')  
            break     
        refresh()
    poolStatus = 'open' 

def conwayTestAnim(_):
    global poolKey
    key0 = poolKey
    land = life.Life()
    
    p = randData(100,100)
    land.setPatternAndChunk(p,12)
    for i in range(0,50):
    
        # anything outside [0 1] is clipped.
        showCells = 0.75 #[0,1]
        showGrid = 0.0 # [0,1].
        showActive = -0.5/3.0 #[0,1,2,3]
        shift = 0.75
    
        im = np.add(np.multiply(land.getPattern(), showCells), np.multiply(land.chunkerBoard(), showGrid))
        im = np.add(im, np.multiply(land.activeBoard(), showActive))
        im = np.add(im,shift)
    
        plotter.clear()
        plotter.imshow(im,cmap='Greys',interpolation='None')
        
        if poolKey is not key0: 
            break 
        refresh()
        
        land.step()
    poolStatus = 'open' 

# All command functions go into this dictionary.
cmds = {'test1': plotTest,
        'test2': plotTestAnim,
        'test3': conwayTestAnim}

def runCmd(_):
    global poolKey
    poolKey = poolKey + 1
    # ALL commands pass through here.
    cmdStrFull = cmdBox.get().lower() # lowercase.
    cmdStr = cmdStrFull.split(" ")
    cmdFn = cmds.get(cmdStr[0])
    if cmdFn == None:
        raise Exception('Unrecognized cmd: '+cmdStr)
    cmdArgs = cmdStr[1:] # empty array for no args.
    closure = lambda: cmdFn(cmdArgs) # run the function object.
    pool.submit(closure)


##################### Activating the main loop #####################
cmdBox.bind('<Return>', runCmd)
root.mainloop() # We never get past this line, instead callbacks are used.






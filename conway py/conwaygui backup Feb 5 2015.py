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

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import random
#import tables
import datetime
#import create_db
from subprocess import call
from imp import reload
import life
from sys import argv
import warnings
import matplotlib.cbook
import numpy as np
from tkinter import *
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

script,h,w,tmax = argv
h = int(h)
w = int(w)
tmax = int(tmax)

# Call this to import it:
call(["python3","setup.py","build_ext","--inplace"])
life = reload(life) # reload it because we built it, the software will have to be ran twice.

plt.ion()

class conwayGUI():
    def __init__(self):
        self.h = h
        self.w = w
        self.tmax = tmax
        self.t = 0
        self.stored = []
        self.paused = False
        self.quitMePlease = False
        self.subSteps = 1 # number of simulation steps/frame.
        self.chunkSize = 12; # Chunks for the simplification code.
        self.land = life.Life()    
    
    # Makes random data for testing the algorythim on:
    def randData(self,x,y):
        out = np.zeros((x,y), np.int)
        for i in range(x):
            for j in range(y):
                out[i,j]= round(random.random()*0.58)
        return out    

    def init_gui(self):
        self.fig = plt.figure()
        gs = gridspec.GridSpec(4,3)
        self.ax1 = self.fig.add_subplot(gs[:,:2])
        self.ax1.set_title('Conway Game of Life Simulator',fontsize=20)
        self.ax2 = self.fig.add_subplot(gs[0,2])
        self.ax3 = self.fig.add_subplot(gs[1,2])
        self.ax4 = self.fig.add_subplot(gs[2,2])
        self.ax5 = self.fig.add_subplot(gs[3,2])
        c = 0
        strings = ['','Play','Pause','Save','Load']
        for ax in self.fig.axes:
            ax.set_xticklabels('')
            ax.set_yticklabels('')
            ax.text(0.3,0.4,strings[c],fontsize=24)
            ax.set_axis_bgcolor('DimGray')
            c+=1
        self.p = self.randData(w,h)
        self.land.setPatternAndChunk(self.p,self.chunkSize)
        self.im = self.ax1.imshow(self.p,cmap='Greys',interpolation='None')
        self.ax6 = self.fig.add_axes([0.05,0.05,0.6,0.075])
        self.ax6.set_xticklabels('')
        self.ax6.set_yticklabels('')
        self.ax6.set_axis_bgcolor('DarkGray')
        self.stats = self.ax6.text(0.1,0.25,'')
        #self.cmdBox = Label( self.fig, text="Type cmds here.")
        
    def onpress(self,fig,event):
        x,y = event.x,event.y
        for ax in fig.axes:
            xa,ya = ax.transAxes.inverted().transform([x,y])
            if xa > 0 and xa < 1 and ya > 0 and ya < 1:
                if ax == self.ax2:
                    self.play()
                if ax == self.ax3:
                    self.pause()
                if ax == self.ax4:
                    self.store_func()
                if ax == self.ax5:
                    self.load()
    
    def get_pattern_numpy(self): # returns a numpy array.
        # anything outside [0 1] is clipped.
        showCells = 0.75 #[0,1]
        showGrid = 0.0 # [0,1].
        showActive = -0.5/3.0 #[0,1,2,3]
        shift = 0.75
    
        im = np.add(np.multiply(self.land.getPattern(), showCells), np.multiply(self.land.chunkerBoard(), showGrid))
        im = np.add(im, np.multiply(self.land.activeBoard(), showActive))
        im = np.add(im,shift)
    
        #im = normalize01(im)
        #print(im.tolist())
    
        return im
    
    def step(self):
       for i in range(self.subSteps):
           self.land.step()
    
             
    def connect(self):
        self.fig.canvas.mpl_connect('close_event',lambda e: self.on_close())
        self.cid = self.fig.canvas.mpl_connect('button_press_event',lambda e: self.onpress(self.fig,e))
    
    def play(self):
        print('Play')
        self.paused = False
        # no need as paused is the flag we use. self.run()
        
    def on_close(self):
        print('Close')
        self.quitMePlease = True
                
    def pause(self):
        print('Paused')
        self.paused = True
        
    def store_func(self):
        print('Saving pattern at timestep {}'.format(self.t))
        self.stored.append(self.p)
        
    def save(self):
        conwaydb = tables.open_file('./conwaydb.h5','a')
        d = str(datetime.date.today())
        d = ''.join(d[2:].split('-'))
        leaves = []
        for leaf in conwaydb.root.simulation._f_walknodes():
            leaves.append(leaf)
        present = False
        for day in leaves:
            if d in day._v_attrs['TITLE']:
                present = True
        if present == True:
            ctb = conwaydb.get_node('/simulation/{}'.format(d))
        elif present == False:
            ctb = create_db.create_table(d,conwaydb)
        for i,pattern in self.stored:
                create_db.add_data(ctb,i,pattern)
        
        
        
    def load(self):
        print('Load not yet implemented')
        
    def disconnect(self):
        self.fig.canvas.mpl_disconnect(self.cid)
        
    def run(self):
        # never leave this loop until the program quits.
        while self.t <= self.tmax:
            if self.quitMePlease:
               break
            plt.draw()
            #if self.paused: break

            if not self.paused:
              self.step()
              self.p = self.get_pattern_numpy()
              self.im.set_array(self.p) # set_array instead of set_data.
              self.stats.set_text('Timestep: {}\nParameters: H: {} W: {} Tmax: {}'.format(self.t,self.h,self.w,self.tmax))
              self.t +=1
            plt.pause(0.05)
        self.save()
        
conway = conwayGUI()
conway.init_gui()
conway.connect()
conway.run()
#plt.close(fig)
        

# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 13:41:22 2016

@author: Will
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import random
import pickle
from sys import argv
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

script,h,w,tmax = argv
h = int(h)
w = int(w)
tmax = int(tmax)

plt.ion()

class conwayGUI():
    def __init__(self,h,w,tmax):
        self.h = h
        self.w = w
        self.tmax = tmax
        self.t = 0
        self.stored = []
        self.paused = False
    
    def get_pattern(self):
        return [[random.randint(0,2) for i in range(self.w)] for j in range(self.h)]

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
        self.p = self.get_pattern()
        self.im = self.ax1.imshow(self.p,cmap='Greys',interpolation='None')
        self.ax6 = self.fig.add_axes([0.05,0.05,0.6,0.075])
        self.ax6.set_xticklabels('')
        self.ax6.set_yticklabels('')
        self.ax6.set_axis_bgcolor('DarkGray')
        self.stats = self.ax6.text(0.1,0.25,'')
        
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
                    
    def connect(self):
        self.cid = self.fig.canvas.mpl_connect('button_press_event',lambda e: self.onpress(self.fig,e))
    
    def play(self):
        print('Play')
        self.paused = False
        self.run()
        
    def pause(self):
        print('Paused')
        self.paused = True
        
    def store_func(self):
        print('Saving pattern at timestep {}'.format(self.t))
        self.stored.append(self.p)
        
    def save(self):
        pickle.dump(self.stored,open('./testing.p','wb'))
        
    def load(self):
        print('Load not yet implemented')
        
    def disconnect(self):
        self.fig.canvas.mpl_disconnect(self.cid)
        
    def run(self):
        while self.t <= self.tmax:
            if self.paused: break
            self.p = self.get_pattern()
            self.im.set_data(self.p)
            self.stats.set_text('Timestep: {}\nParameters: H: {} W: {} Tmax: {}'.format(self.t,self.h,self.w,self.tmax))
            plt.draw()
            plt.pause(0.05)
            self.t +=1
        self.save()
        
conway = conwayGUI(h,w,tmax)
conway.init_gui()
conway.connect()
conway.run()
if conway.t >= conway.tmax:
    conway.disconnect()
        

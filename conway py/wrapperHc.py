# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 19:01:58 2016

@author: Will
"""
'''Wrapper Function for hillClimb.py'''
from hillClimbWrapped import *


w = 50 # pattern size.
h = 150
chunk = 10 # MUST divide evenly with h or it may make a coorder that is debries-free.

# parameters for our environment:
worldW = 500 # entire width.
density = 0.1 # density of space junk.

mute = [0.01,0.025,0.05,0.075,0.1]
for j in mute:  
    # Core algorithm parameters:
    time = 10000# how long we run before timing out.
    initPatternDensity = 0.15 # initial random density.
    replicates = 3# how many to average for the fitness function.
    mutateRate = j # pointwise mutation.
    reuseFitness = False # Never recalculate a fitness on a pattern if true.
    N = 200
    
    climber = hillClimb(w,h,chunk,worldW,density,time,initPatternDensity,replicates,mutateRate,reuseFitness,N)
    climber.run()
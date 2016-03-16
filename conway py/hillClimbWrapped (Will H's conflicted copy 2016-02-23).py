# game.py - 3/22/2013

import numpy as np
import random
import life
from random import randint
import matplotlib.pyplot as plt
from multiprocessing import Pool
from functools import partial # gets around the not pickleable.
import functools
import datetime
import os
import pickle

def get_header():
    '''Get timestamp and random seed to store at end of sim. Check if day exists'''
    now = datetime.datetime.now()
    ts = {'Day':now.strftime('%m%d%y'),'Timestamp':now.strftime('%H%M%S')}
    random.seed()
    s = random.getstate()
    random.setstate(s)
    if os.path.isfile(ts['Day']+'.p'):
        with open(ts['Day']+'.p','rb') as rp:
            data = pickle.load(rp)
            data[ts['Day']][ts['Timestamp']] = {'Parameters':[s],'Patterns':[]}
    elif  not os.path.isfile(ts['Day']+'.p'):
            data = {ts['Day']:{ts['Timestamp']:{'Parameters':[s],'Patterns':[]}}}
    return data,ts

def save(data,ts):
    '''Save all patterns in pickle. One pickle per day. Structure is nested dict.
    Day is key, timestamp of each sim is value. each timestamp is, in turn,
    a key for a dict and values are the patterns at t0 and their final fitnesses'''
    with open(ts['Day']+'.p','wb') as wp:
        pickle.dump(data,wp)
    print('Data from simulation {}-{} pickled!'.format(ts['Day'],ts['Timestamp']))

def isclear(pattern, x, y, pw, ph):
    # determines whether it's safe to add a still life-pattern to a still-life environment.
    # x and y are our pattern's upper-left (lowest x and y index) corner and pw and ph are our pattern's extents.

    patW = np.shape(pattern)[0]
    patH = np.shape(pattern)[1]
    xindex = range(max(x-2,0),min(x+pw+2,patW)) # suppress wrap.
    yindex = range(y-2,y+ph+2)

    #doing pattern[xindex, yindex], but with wrap.
    clear = True
    for x in xindex:
        for y in yindex:
            if pattern[x][y%patH]>0:
                clear = False
    return clear

def addDebris(pattern, w, h, worldW, density):
    # adds debris (blocks for now). A buffer of two spaces prevents debris from intersecting.
    nNeed = 0.25*(worldW-w)*h*density # how many we need.
    nHave = 0
    pattern0 = np.zeros((worldW,h),np.int)
    pattern0[0:w, 0:h] = pattern
    while nHave < nNeed:
       # pick a random point.
       rx = randint(w,worldW-2) # indexes are inclusive.
       ry = randint(0,h-1)

       #print(self.isclear(pattern0,rx,ry,2,2))
       if isclear(pattern0,rx,ry,2,2)==True:
           pattern0[rx,ry] = 1
           pattern0[rx,(ry+1) % h] = 1
           pattern0[rx+1,ry] = 1
           pattern0[rx+1,(ry+1) % h] = 1
           nHave = nHave + 1
    return pattern0

def run(pattern, time, chunk):
    # runs conways life on this pattern, returns the final pattern.
    land = life.Life()
    land.setPatternAndChunk(pattern,chunk)
    for i in range(time):
        land.step()
    pattern1 = land.getPattern()
    return pattern1

def score(pattern0, pattern1, w, h, worldW):
    # fitness function: the right-most influence:
    if np.shape(pattern1) != np.shape(pattern1):
       throw("Pattern size does not devide into chunk.")

    diff = np.subtract(pattern1,pattern0)
    maxInd = 0
    for i in range(0,worldW):
       for j in range(0,h):
          if diff[i][j] != 0:
             maxInd = i
    return maxInd-w

def trial(seed, pattern, w, h, worldW, density, time, chunk):
    # Runs pattern returns the fitness.
    # TODO: use the seed argument.
    pattern0 = addDebris(pattern, w, h, worldW, density)

    pattern1 = run(pattern0, time, chunk)

    return score(pattern0, pattern1, w, h, worldW)


class hillClimb:

    def __init__(self,w,h,chunk,worldW,density,time,initPatternDensity,replicates,mutateRate,reuseFitness,N):
        # Parameters for our evolution.
        self.w = w # pattern size.
        self.h = h
        self.chunk = chunk # MUST divide evenly with h or it may make a coorder that is debries-free.

        # parameters for our environment:
        self.worldW = worldW # entire width.
        self.density = density # density of space junk.

        # Core algorithm parameters:
        self.time = time # how long we run before timing out.
        self.initPatternDensity = initPatternDensity # initial random density.
        self.replicates = replicates # how many to average for the fitness function.
        self.mutateRate = mutateRate # pointwise mutation.
        self.reuseFitness = reuseFitness # Never recalculate a fitness on a pattern if true.
        self.N = N
        
        self.pattern = np.zeros((self.w,self.h), np.int)
        for i in range(0,self.w):
           for j in range(0,self.h):
               if random.random()<self.initPatternDensity:
                   self.pattern[i][j] = 1

    def showPattern(self,pattern):
        # shows a pattern.
        plt.imshow(pattern)
        plt.show()

    def multiTrial(self, pool, show=None):
        # runs num independent trials and returns the fitness (how far any change was made).
        # This function is random so it will give different results each time.
        # TODO: store random seeds in the result for complete perfect reproducibility.

        num = self.replicates

        pattern = self.pattern
        w = self.w
        h = self.h
        worldW = self.worldW
        density = self.density
        time = self.time
        chunk = self.chunk

        if show:
            if num>1:
                throw("Show=true only works when we do one trial")

            pattern0 = addDebris(pattern, w, h, worldW, density)
            pattern1 = run(pattern0, time, chunk)
            sc = score(pattern0, pattern1, w, h, worldW)

            mode = 'init-fin' # Final pattern with initial as ghost.
            mode = 'cloudy-timelapse' # Timelapse that looks like coulombs clouds.
            if mode=='init-fin':
                self.showPattern(np.add( np.multiply(pattern1,10), pattern0))

            if mode=='cloudy-timelapse': # run again, in slow mo!
                land.setPatternAndChunk(pattern0,self.chunk)
                acc = pattern0
                skip = 10
                for i in range(round(self.time/skip)):
                   for j in range(skip):
                       land.step()
                   acc = np.add(acc, land.getPattern())
                self.showPattern(acc)

            sc = score(pattern0, pattern1, w, h, worldW)
            print(sc)

        else: # Now with multithreading.
            multithread = True
            #UNPICKALLEBAL, wont work: fitnessFn = lambda: trial(pattern, w, h, worldW, density, time, chunk)
            # TODO: have some random offset for seeds, etc that is brought into this function.
            fitnessFn = partial(trial,pattern=pattern,w=w,h=h,worldW=worldW,density=density,time=time,chunk=chunk)

            if multithread:
                fitnesses = list(pool.map(fitnessFn, range(num)))
            else:
                fitnesses = list(map(fitnessFn, range(num)))
            return functools.reduce(lambda x, y: x + y, fitnesses) / len(fitnesses)

    def mutate(self):
        for i in range(0,self.w):
           for j in range(0,self.h):
               if random.random()<self.mutateRate:
                   self.pattern[i][j] = 1- self.pattern[i][j]

    def store(self,pattern,fitness):
        self.data[self.ts['Day']][self.ts['Timestamp']]['Patterns'].append((pattern,fitness))




    def climb(self, fitness, pool): # nAverage = number of trials to average to evaluate fitness.
        # Tries a new pattern. Picks it if better.

        nAverage = self.replicates

        oldPattern = np.copy(self.pattern)

        if self.reuseFitness and (fitness is not None):
            oldScore = fitness
        else:
            oldScore = self.multiTrial(pool)
            #MLA here
        self.mutate()

        newScore = self.multiTrial(pool)
        # Replace if it is more:
        if newScore >= oldScore:
            self.pattern = self.pattern # keep new pattern by doing nothing.
            self.store(self.pattern,newScore)
            return newScore
        else:
            self.pattern = oldPattern # old pattern.
            self.store(self.pattern,oldScore)
            return oldScore
            
    def run(self,multi=True):
        '''Wrapper to run climber. multi arg False means single is True'''
        data,ts = get_header()
        self.data = data
        self.ts = ts
        self.data[self.ts['Day']][self.ts['Timestamp']]['Parameters'].append([self.w,self.h,self.chunk,self.worldW,self.density,self.time,self.initPatternDensity,self.replicates,self.mutateRate,self.reuseFitness,self.N])

        pool = Pool(processes=4)
        
        if not multi:
            fitness = self.multiTrial(1,pool,True)
            print(fitness)
        
        if multi:
            fitness = np.zeros(self.N, np.int)
            fit = None # force it to calculate the fitness.
            for i in range(self.N):
                fit = self.climb(fit, pool)
                fitness[i] = fit
                print('fitness: ',fitness[i],' ',i,' out of ',self.N)
            plt.plot(fitness)
            plt.show()
        save(self.data,self.ts)




# Note: better climbing with 0.01 initial random not 0.5 because empty space is bad.
# Optimizations:
#   Multithread the embarrassingly parallel fitness calculation.
#   Reusing vs not reusing patterns' fitness values.

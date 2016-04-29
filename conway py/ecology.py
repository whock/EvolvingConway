# Ecology class that determines how well which organisms do.
# "how well they do" depends on random # generators, so this also includes ways to generate
# consistant rngs.
# game.py - 3/22/2013

import numpy as np
import random

from random import randint
import matplotlib.pyplot as plt
from functools import partial # gets around the not pickleable.
import functools
from numpy.random import RandomState
import pmap
from subprocess import call#, reload
import copy

import fill

#call(["python3","setup.py","build_ext","--inplace"])
print('WARNING: no attempt made to update the cython code. IF YOU WANT TO RELOAD: uncomment above line (line #20), run, then restart python to update.')

# TODO: check to make sure python isn't less up-to-date.

import life # AFTER the call.
#life = reload(life) # reload it because we built it BUT the software will have to be ran twice!


class Sentinel():
    '''creates a callable object which can be called within any fx to store data
    pass the sentinel a tuple of tuples ('name',value) where value is an iterable
    -- 'data'
    -- 'metadata'
    -- 'pattern'
    and the rest of the arguments are the data to be stored
    example use: sniff('data',[109,111,110,123])
    '''
    def __init__(self):
        self.data = {'data' = [],'metadata' = [], 'patterns' = []}
        self.counter = 0
    def __call__(self,*args):
        self.counter += 1
        for item in args:
            self.data[item[0]] = (self.counter,item[1])

sentinel = Sentinel()


# makes a problem (that the climber has to solve):
def makeProblem(**kwargs):
    defaults = {'w': 120, 'h': 144, 'chunk':12, 'worldW': 504, 'density': 0.02,
                'time': 10000, 'rng': RandomState(3210123)}
    return fill.fill(kwargs, defaults)

def copyRng(rng):
    # Copies a random number generator. Should be deep.
    rs = RandomState(0)
    rs.set_state(rng.get_state()) # doesn't depend on seeds, works even with different seeds.
    return rs

def newRng(seed):
    return RandomState(seed)

def nextSeed(rng):
    rng = copyRng(rng)
    return rng.randint(0,2147483647)

def nextSeedFromCurrentSeed(seed):
    return nextSeed(RandomState(seed))

def nextRng(rng): # generates a new RNG by making a random seed from the current rng.
    # Don't generate a new rng every random number. Instead, batch random #'s.
    return RandomState(nextSeed(rng))

def _sidewaysNextRng(rng):
    # Like nextRng but taking a different path.
    # We can generate a list of rngs from a single rng you supply, and a completly different list
    # of rngs from your nextRng().
    rng = copyRng(rng) # side-effect free.
    f1 = rng.rand() # any sequence that puts the rng into a different state and is somewhat hard to accidentily guess.
    f2 = rng.rand()
    return RandomState(nextSeed(rng))

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

def addDebris(pattern, w, h, worldW, density, rng):
    # adds debris (blocks for now). A buffer of two spaces prevents debris from intersecting.
    rng = copyRng(rng)
    nNeed = 0.25*(worldW-w)*h*density # how many we need.
    nHave = 0
    pattern0 = np.zeros((worldW,h),np.int)
    #print("w",w,"h",h,"sz",pattern.shape,'sz0',pattern0.shape)
    pattern0[0:w, 0:h] = pattern
    while nHave < nNeed:
       # pick a random point.
       rx = rng.randint(w,worldW-2) # indexes are inclusive.
       ry = rng.randint(0,h-1)

       #print(self.isclear(pattern0,rx,ry,2,2))
       if isclear(pattern0,rx,ry,2,2)==True:
           pattern0[rx,ry] = 1
           pattern0[rx,(ry+1) % h] = 1
           pattern0[rx+1,ry] = 1
           pattern0[rx+1,(ry+1) % h] = 1
           nHave = nHave + 1
    return pattern0

def conway(pattern, time, chunk):
    # runs conways life on this pattern (i.e. one that includes debris), returns the final pattern.
    land = life.Life()
    land.setPatternAndChunk(pattern,chunk)
    for i in range(time):
        land.step()
    pattern1 = land.getPattern()
    return pattern1

def mostRightward(pattern0, pattern1, w, h, worldW):
    # fitness function: the right-most influence:
    if np.shape(pattern1) != np.shape(pattern1):
       throw("Pattern size does not devide into chunk.")

    diff = np.subtract(pattern1,pattern0)
    maxInd = 0
    for i in range(0,worldW): # ok not the most performant.
       for j in range(0,h):
          if diff[i][j] != 0:
             maxInd = i
    return maxInd-w

def singleTrial(pattern, problem):
    # Generates pattern, returns the fitness.
    pattern0 = addDebris(pattern, problem['w'], problem['h'], problem['worldW'], problem['density'], problem['rng'])
    pattern1 = conway(pattern0, problem['time'], problem['chunk'])
    return mostRightward(pattern0, pattern1, problem['w'], problem['h'], problem['worldW'])

def getMultiTrialRngs(rng, n):
    # Make a stream of rngs (NOT using next, because they probably will use nnextRng) that are used
    # for each trial.
    rngs = list()
    r = rng
    for i in range(n):
        r = _sidewaysNextRng(r)
        rngs.append(r)
    return rngs

def fitness(problem, pattern, n): # Runs n trials.
    rngs = getMultiTrialRngs(problem['rng'], n) # one for each trial.

    # Put one rng into each problem:
    problems = list()
    for i in range(n):
        problem1 = copy.copy(problem)
        problem1['rng'] = rngs[i]
        problems.append(problem1)

    parallel = True

    if parallel: # multithread.
        fitnesses = list(pmap.maplist(singleTrial, pmap.box(pattern), problems))
    else:
        fitnesses = list(map(lambda p: singleTrial(pattern, p), problems))
    return_this = functools.reduce(lambda x, y: x + y, fitnesses) / n
    sentinel(('data',return_this),('pattern',pattern),('problem',problem))
    return return_this

def showPattern(pattern): # shows a pattern (only works for a figure).
    plt.imshow(pattern)
    plt.show()

def viewTrial(problem, pattern, n, mode): # graphical tool to see what is going on.
    rngs = getMultiTrialRngs(problem['rng'], n) # one for each trial.
    f, axs = plt.subplots(n)

    for i in range(n):
        pattern0 = addDebris(pattern, problem['w'], problem['h'], problem['worldW'], problem['density'], rngs[i])
        pattern1 = run(pattern0, problem['time'], problem['chunk'])
        ax = axs[i]
        if mode=='init-fin':
            ax.imshow(np.add( np.multiply(pattern1,10), pattern0))
        if mode=='cloudy-timelapse': # run again, in slow mo!
            land = life.Life()
            land.setPatternAndChunk(pattern0,problem['chunk'])
            acc = pattern0
            skip = 10
            for i in range(round(problem.time/skip)):
                for j in range(skip):
                    land.step()
            acc = np.add(acc, land.getPattern())
            ax.imshow(acc)
        sc = score(pattern0, pattern1, problem['w'], problem['h'], problem['worldW'])
        ax.set_title('Trial # '+str(i)+' fitness: '+str(sc))
    plt.show()

def add_to_database():
    pass


def run(problem, hyperGeno, genos, nextGenosFn, nStep):
    """The main run function.
        nextGenosFn is (hyperGeno, genos, problem) => genos."""

    problem = copy.copy(problem)
    for i in range(nStep):
        genos = nextGenosFn(hyperGeno, genos, problem)
        problem['rng'] = nextRng(problem['rng']) # Important part.
    return genos

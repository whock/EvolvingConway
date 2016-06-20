# Ecology class that determines how well which organisms do.
# "how well they do" depends on random # generators, so this also includes ways to generate
# consistant rngs.

# Note on random numbers: We use sha hashes to generate new seeds and then numpys rngs.

# game.py - 3/22/2013

import numpy as np

import hashlib
import matplotlib.pyplot as plt
from functools import partial # gets around the not pickleable.
import functools
from numpy.random import RandomState
import pmap
from subprocess import call#, reload
import copy
from conway_sql import *
import graph

#import conwaygui

import fill

#call(["python3","setup.py","build_ext","--inplace"])
print('WARNING: no attempt made to update the cython code. IF YOU WANT TO RELOAD: uncomment above line (line #23), run, then restart python to update.')

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
        self.data = {'data': [],'metadata': [], 'patterns': [], 'problems': []}
        self.counter = 0
    def __call__(self,*args):
        self.counter += 1
        for item in args:
            self.data[item[0]].append((self.counter,item[1]))

sentinel = Sentinel()

def sha224Int(x, salt):
    # hash of x, for extra randomness (ot used to generate random numbers, used to make random number generators).
    # Returns 32 bit in format so that numpy's rngs work.
    xs = str(x) + salt
    h = hashlib.sha224(xs.encode()).hexdigest()
    xLong = int(h,16)
    return xLong & 0xffffffff # 32 bit unsigned int.

def copyRng(rngs):
    # Copies a random number generator (a list of rngs). Should be deep.
    out = []
    for r in rngs:
        rs = RandomState(0)
        rs.set_state(r.get_state()) # doesn't depend on seeds, works even with different seeds.
        out.append(rs)
    return out

def newRng(seed):
    # Seeds an rng. Seed can be a number or a list of integers. 
    # Returns a list of rngs. We apply a hash digest to the seed.
    if (type(seed) is not list) and (type(seed) is not tuple):
        seed = [seed]
    out = []
     
    s0 = ""
    for i in range(len(seed)):
        s0 = s0 + str(seed[i])
    
    for i in range(len(seed)):
        # EACH new seed is a DIFFERENT function of ALL the old seeds.
        out.append(RandomState(sha224Int(seed[i],"newRngSalt "+str(i)+s0)))
    return out

# makes a problem (that the climber has to solve):
def makeProblem(**kwargs):
    # 8 rngs to make it extremly hard that we get the same one twice (birthday 2^(4*32))
    #  numpys rngs are limited to 32 bits, so use multible to make the randomness more robust.
    defaults = {'w': 120, 'h': 144, 'chunk':12, 'worldW': 648, 'density': 0.02,
                'time': 10000, 'seed': [1234,2345,3456,4567,5678,6789,7890,89011]}
    return fill.fill(kwargs, defaults)

def randintBANG(rngs, lo, hi):
    # Generates one int from an rng pack, modifying the rngs in the process.
    # Under the "rngs are perfect" assumption (close enough in practice for non crypto):
    # Subsequent calls are statistically independent.
    # Two different rng packs generate statistically independent random numbers as long as
    # at least one rng is independent from any others in the pack.
    # Rng packs with multiple seeds are much more robust.
    out = 0
    d = hi-lo + 1
    for r in rngs:
        out = out + r.randint(0,hi-lo) # overflow is not an issue: we use high precision ints.
    return (out % d) + lo

def randBANG(rngs, h, w):
    # Like randint but generates a float array from the rng pack. 
    out = np.zeros((h,w), dtype=np.double)
    for r in rngs:
        out = out + r.rand(h,w)
    return np.mod(out, 1.0)

def nextSeed(seed, dir): #KEY FUNCTION: allows branching different random #s in different directions.
    # Gets the next seed along direction dir (which is converted into a string).
    # Each unique string is a different dir crypto-almost-surely.
        # Make the seeds:
    if (type(seed) is not list) and (type(seed) is not tuple):
        seed = [seed]    
    out = []
    for s in seed:
        out.append(sha224Int(s, dir))
    return out

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

def addDebris(pattern, w, h, worldW, density, seed):
    # adds debris (blocks for now). A buffer of two spaces prevents debris from intersecting.
    rngs = newRng(seed)
    nNeed = 0.25*(worldW-w)*h*density # how many we need.
    nHave = 0
    pattern0 = np.zeros((worldW,h),np.int)
    #print("w",w,"h",h,"sz",pattern.shape,'sz0',pattern0.shape)
    pattern0[0:w, 0:h] = pattern
    while nHave < nNeed:
       # pick a random point.
       rx = randintBANG(rngs,w,worldW-2) # indexes are inclusive.
       ry = randintBANG(rngs,0,h-1)

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

def singleTrialBeforeVsAfter(pattern, problem, metric):
    """ Single trial before vs after.
         Metric takes in (pattern0, pattern1, w, h, worldW) and calculates any scalar. """
    # Generates pattern, returns the fitness.
    pattern0 = addDebris(pattern, problem['w'], problem['h'], problem['worldW'], problem['density'], problem['seed'])
    pattern1 = conway(pattern0, problem['time'], problem['chunk'])
    return metric(pattern0, pattern1, problem['w'], problem['h'], problem['worldW'])

def _getMultiTrialSeeds(seed, n):
    # Make a stream of rngs (using _sideways, because they probably will use nnextRng) that are used
    # for each trial. Do NOT call this externally. This is our very own direction.
    seeds = []
    seedi = seed
    privateSalt = 'Unique to _getMultiTrialSeeds in ecology.py, dont use this string elsewhere. '
    privateSalt = privateSalt+'9qr0me8r092m3409cm'
    for i in range(n):
        seedi = nextSeed(seedi, privateSalt)
        seeds.append(seedi)
    return seeds

def vectorBeforeVsAfter(problem, pattern, metric, n):
    """ Calculates a vector of values of metric for the problem and pattern, using 
        a sequence of random number generators.
        Metric takes in (pattern0, pattern1, w, h, worldW) and calculates any value.
        Metric CANNOT be a lambda function due to limits to python """ 
    # IMPORTANT: multithread using the same random # generator could make non-repeatable results.
    seeds = _getMultiTrialSeeds(problem['seed'], n) # one for each trial.
    # Put one rng into each problem:
    problems = list()
    for i in range(n):
        problem1 = copy.copy(problem)
        problem1['seed'] = seeds[i]
        problems.append(problem1)
    parallel = True
    if parallel: # multithread.
        scores = list(pmap.maplist(singleTrialBeforeVsAfter, pmap.box(pattern), problems, pmap.box(metric)))
    else:
        scores = list(map(lambda p: singleTrialBeforeVsAfter(pattern, p, metric), problems))
    sentinel(('data',scores),('patterns',pattern),('problems',problem))
    return scores    

def averageBeforeVsAfter(problem, pattern, metric, n):
    """ Calculates the average of metric for the problem and pattern.
        Metric takes in (pattern0, pattern1, w, h, worldW) and calculates any scalar.
        Metric CANNOT be a lambda function due to limits to python """
    scores = vectorBeforeVsAfter(problem, pattern, metric, n)
    return_this = functools.reduce(lambda x, y: x + y, scores) / n
    sentinel(('data',return_this),('patterns',pattern),('problems',problem))
    return return_this
    
def fitness(problem, pattern, n): # Runs n trials.
    return averageBeforeVsAfter(problem, pattern, mostRightward, n)

def showPattern(pattern): # shows a pattern (only works for a figure).
    plt.imshow(pattern)
    plt.show()

def viewTrial(problem, pattern, n, mode): # graphical tool to see what is going on.
    
    seeds = _getMultiTrialSeeds(problem['seed'], n) # one for each trial.
    imgs = []
    titles = []

    for i in range(n):
        pattern0 = addDebris(pattern, problem['w'], problem['h'], problem['worldW'], problem['density'], seeds[i])
        pattern1 = conway(pattern0, problem['time'], problem['chunk'])
        if mode=='init-fin':
            imgs.append(np.add( np.multiply(pattern1,10), pattern0))
        if mode=='cloudy-timelapse': # run again, in slow mo!
            land = life.Life()
            land.setPatternAndChunk(pattern0,problem['chunk'])
            acc = pattern0
            skip = 10
            for i in range(round(problem.time/skip)):
                for j in range(skip):
                    land.step()
            acc = np.add(acc, land.getPattern())
            imgs.append(acc)  
        sc = mostRightward(pattern0, pattern1, problem['w'], problem['h'], problem['worldW'])  
        titles.append('Trial # '+str(i)+' fitness: '+str(sc))
    
    return graph.multiImagePlot(imgs, titles) # can't import conway directly, it crashes.


def run(problem, hyperGeno, genos, nextGenosFn, nStep):
    """The main run function.
        nextGenosFn is (hyperGeno, genos, problem) => genos."""
    problem = copy.copy(problem)
    privateSalt1 = 'Another only in to ecology.py, dont use this string elsewhere.'
    privateSalt1 = privateSalt1+'sdfdgtr43ewdsfgtrewdsf'
        
    for i in range(nStep):
        genos = nextGenosFn(hyperGeno, genos, problem)
        problem['seed'] = nextSeed(problem['seed'], privateSalt1) # Keep changing the problem so that the debris is different each time.
    save_sentinel(sentinel)
    return genos

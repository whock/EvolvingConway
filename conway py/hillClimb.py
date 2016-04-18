# game.py - 3/22/2013

import ecology

import fill
import copy

import numpy as np

def hyperGenotype(**kwargs):
    """ Creates a set of hyper parameters that is used for evolving but does not change as evolution progresses. """
    defaults = {'initDensity': 0.5, 'replicates': 12, 'mutateRate': 0.07, 'reuseFitness': False, 'seed': 12345}
    return fill.fill(kwargs, defaults)
  
def singleGenotype(hyperGenotype):
    return {'pattern': np.zeros([0,0], np.int), 'rng': ecology.newRng(hyperGenotype['seed']),
              'fitness': None, 'fillDensity': hyperGenotype['initDensity']}
    
def initGenotypes(hyperGenotype): 
    """ Creates an initial population (an array) from the hyperGenotype. """
    return singleGenotype(hyperGenotype) # only one genotype.

def phenotype(geno, problem):
    """ Creates the phenotype (the pattern) from the interaction of genotype + environment (the problem).
     Also returns the (maybe) modified rng as the second argument in the tuple."""
    w = problem['w']
    h = problem['h']
    pattern0 = geno['pattern']
    w0 = pattern0.shape[0]
    h0 = pattern0.shape[1]
    pattern = np.zeros([w,h], np.int)
    pattern[0:min(w, w0), 0:min(h, h0)] = pattern0[0:min(w, w0), 0:min(h, h0)]
    
    if w > w0 or h >h0: # Fill in fresh pixels.
        rng = ecology.copyRng(geno['rng'])
        rnds = rng.rand(max(0, w-w0), max(0, h-h0))
        pattern[w0:w, h0:h] = np.greater(rnds, 1.0-geno['fillDensity'])
    
    return (pattern, rng)
 
def pointwiseMutate(pattern, rng, mutateRate):
    """ Each pixel has a chance of changing """
    rng = ecology.copyRng(rng)
    pattern = np.copy(pattern)    
    changePixel = np.greater(rng.rand(pattern.shape()), 1.0-mutateRate)
    
    return (pattern + changePixel*(1-2*pattern), rng)    

def nextGenotypes(hyperGeno, genos, problem):
    """ Computes the next set of genotypes from the hyper params, the current genotype, and the problem."""
    geno = genos # only one genotype.
    geno['dotsX'] = np.copy(geno['dotsX'])
    geno['dotsY'] = np.copy(geno['dotsY'])
    geno['rng'] = ecology.copyRng(geno['rng'])
    w = problem['w']
    h = problem['h']
    
    if hyperGeno['reuseFitness'] and geno['fitness'] is not None:
        oldScore = geno['fitness']
    else:
        (oldPattern, geno['rng']) = phenotype(geno, problem)
        oldScore = ecology.fitness(problem, oldPattern, hyperGeno['replicates'])
    (newPattern, geno['rng']) = pointwiseMutate(oldPattern, geno['rng'], hyperGeno['']) 
    
    # We DO reuse the problem's debris between the old and new fitnesses, but not across generations of course:
    newScore = ecology.fitness(problem, newPattern, hyperGeno['replicates'])
    if newScore>=oldScore: # it's better so replace the pattern.
        geno['pattern'] = newPattern
    return geno
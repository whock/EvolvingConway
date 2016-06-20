# game.py - 3/22/2013

import ecology

import fill
import copy
import genetics
import grader

import numpy as np

def hyperGenotype(**kwargs): #### KEY FUNCTION.
    """ Creates a set of hyper parameters that is used for evolving but does not change as evolution progresses. """
    defaults = {'initDensity': 0.5, 'replicates': 12, 'mutateRate': 0.07, 'reuseFitness': False, 'moment':float("inf"), 'seed': [1,2,3,4,5,6,7,8]}
    return fill.fill(kwargs, defaults)
  
def singleGenotype(hyperGenotype):
    # NOTE: rngs need to be in the genotype to stay fresh and change each generation
    # However, they are not optimized on. Same idea with fitness.
    return {'pattern': np.zeros([0,0], np.int), 'seed': ecology.nextSeed(hyperGenotype['seed'],"hillClimb.singleGenotype, Setting the single genotype form the hyper genotype."),
              'fitness': None, 'fillDensity': hyperGenotype['initDensity']}
    
def initGenotypes(hyperGenotype): #### KEY FUNCTION. 
    """ Creates an initial population (an array) from the hyperGenotype. """
    return singleGenotype(hyperGenotype) # only one genotype. 

def nextGenotypes(hyperGeno, genos, problem): #### KEY FUNCTION.
    """ Computes the next set of genotypes from the hyper params, the current genotype, and the problem."""
    geno = genos # only one genotype.
    geno = geno.copy() # don't modify the original.
    
    w = problem['w']
    h = problem['h']
    
    if hyperGeno['reuseFitness'] and geno['fitness'] is not None:
        oldScore = geno['fitness']
    else:
        geno['seed'] = ecology.nextSeed(geno['seed'], "hillClimb.nextGenotypes, Change the seed for the gene expression step.")
        oldPattern = genetics.oneToOne(geno, problem)
        oldScore = ecology.fitness(problem, oldPattern, hyperGeno['replicates'])
        geno['fitness'] = oldScore
    newPattern = genetics.pointwiseMutate(oldPattern, geno['seed'], hyperGeno['mutateRate']) 
    geno['seed'] = ecology.nextSeed(geno['seed'], "hillClimb.nextGenotypes, After pointwise mutation update the hillcClimb seed.")
    
    # We DO reuse the problem's debris between the old and new fitnesses, but not across generations of course:
    if hyperGeno['moment']==float("inf"):
        newScore = grader.maxDist(problem, newPattern, hyperGeno['replicates']) # 1:1 with fitness.
    elif hyperGeno['moment']==1:
        newScore = grader.firstMoment(problem, newPattern, hyperGeno['replicates']) # Will a softer one be better?
    else:
        raise ValueError('moment must be 1 or float("inf")')
    if newScore>=oldScore: # it's better so replace the pattern.
        geno['pattern'] = newPattern
        geno['fitness'] = newScore
    return geno
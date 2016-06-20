# Different ways to "grade" the patterns. 
import numpy as np
import ecology

def firstMomentCalc(pattern0, pattern1, w, h, worldW):
    # fitness function: the right-most influence:
    if np.shape(pattern1) != np.shape(pattern1):
       throw("Pattern size does not devide into chunk.")

    diff = np.subtract(pattern1,pattern0)
    totalMoment = 0.0
    for i in range(w,worldW): # ok not the most performant.
       for j in range(0,h):
          if diff[i][j] != 0:
             totalMoment = totalMoment+1.0
    return totalMoment

def maxDist(problem, pattern, replicates):
    """ Maximum distance, the same metric that is the final fitness. """
    return ecology.fitness(problem, pattern, replicates)

def firstMoment(problem, pattern, replicates):
    """ Maximum distance, the same metric that is the final fitness. """
    return ecology.averageBeforeVsAfter(problem, pattern, firstMomentCalc, replicates)
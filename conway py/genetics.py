# Basic genetic functions.
import numpy as np
import ecology

def oneToOne(geno, problem): # semi-key function.
    """ Creates the phenotype (the pattern) from the interaction of genotype + environment (the problem).
     We still need an rng to and density to fill in exta space."""
    w = problem['w']
    h = problem['h']
    pattern0 = geno['pattern']
    w0 = pattern0.shape[0]
    h0 = pattern0.shape[1]
    pattern = np.zeros([w,h], np.int)
    pattern[0:min(w, w0), 0:min(h, h0)] = pattern0[0:min(w, w0), 0:min(h, h0)]
    
    rngs = ecology.newRng(geno['seed'])
    if w > w0 or h >h0: # Fill in fresh pixels.
        rnds = ecology.randBANG(rngs, max(0, w-w0), max(0, h-h0))
        pattern[w0:w, h0:h] = np.greater(rnds, 1.0-geno['fillDensity'])
    return pattern

def pointwiseMutate(pattern, seed, mutateRate):
    """ iid chance of changing each pixel by mutateRate. """
    rngs = ecology.newRng(seed)
    pattern = np.copy(pattern)    
    changePixel = np.greater(ecology.randBANG(rngs, pattern.shape[0], pattern.shape[1]), 1.0-mutateRate)
    
    return pattern + changePixel*(1-2*pattern) 
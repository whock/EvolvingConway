# game.py - 3/22/2013

import ecology

import fill
import copy

# Makes a climber with a random seed:
def makeClimber(**kwargs):
    defaults = {'initDensity': 0.5, 'replicates': 12, 'mutateRate': 0.07, 'reuseFitness': False, 'seed': 12345}
    geno = fill.fill(kwargs, defaults)
    return {'geno': geno}

def initPattern(width, height, density): # TODO: use seed.
   pattern = np.zeros((width,height), np.int) # Does not include debris.
   for i in range(0,width):
      for j in range(0,height):
          if random.random()<density:
              pattern[i][j] = 1

def mutate(pattern0, mutationRate, rng): # TODO: use the seed. 
    pattern = np.copy(pattern0);
    w = size(pattern,1);
    h = size(pattern,2);
    for i in range(0,w):
        for j in range(0,h):
            if rng.rand()<mutationRate:
               pattern[i][j] = 1-pattern[i][j]
    return pattern

def step(problem, climber, pool):
    """The main step function. The general format for step functions is
       [problem, pop, pool] => new pop. In our case pop is just a single climber."""
    climber = copy.copy(climber) # don't modify the original copy.
    climber['pheno'] = copy.copy(climber['pheno']) # one more level of copying down needed.
    
    geno = climber['geno']
    # initialize the pattern if not done so before:
    if not ('pheno' in climber):
        pheno = dict()
        pheno['pattern'] = initPattern(climber['initDensity'])
        pheno['fitness'] = None
        pheno['rng'] = RandomState(geno['seed'])
    else:
        pheno = climber['pheno']
    climber['pheno'] = pheno
    
    n = geno['replicates']
    oldPattern = np.copy(pheno['pattern'])

    rng1 = ecology.nextRng(pheno['rng'])
    if geno['reuseFitness'] and (pheno['fitness'] is not None):
        oldScore = fitness
    else:
        oldScore = ecology.fitness(problem, pheno['pattern'], rng1, n, pool)
    rng2 = ecology.nextRng(rng1)
    pattern1 = mutate(pheno['pattern'], pheno['mutateRate'], rng2)

    rng3 = ecology.nextRng(rng2)
    newScore = ecology.fitness(problem, pattern, rng3, n, pool)
    
    pheno['rng'] = ecology.nextRng(rng3) # probably we can just use rng3, but taking the next one is safe.
    
    # Replace the pattern if we improve:
    if newScore >= oldScore:
        pheno['pattern'] = pattern1
        
    return climber
# self-contains test/demonstration functions.
import taskMgr
import hillClimb
import ecology
import genetics
import time
import math
import numpy as np

def testFitness():
    hyper = hillClimb.hyperGenotype()
    geno = hillClimb.initGenotypes(hyper)
    problem = ecology.makeProblem()
    (pattern, _) = genetics.oneToOne(geno, problem)
    n = 4
    score = ecology.fitness(problem, pattern, n)
    mode = 'init-fin'
    # mode = 'cloudy-timelapse'
    vt = ecology.viewTrial(problem, pattern, n, mode) # this part takes a few seconds.
    return {'result': score, 'gui': vt}

def hillClimbFromBadStart():
    # Runs the hillclimber from a bad start, making it easier to show improvement.
    pool = taskMgr.getPool()
    hyperGeno = hillClimb.hyperGenotype(initDensity=0.01, mutateRate=0.04)
    problem = ecology.makeProblem()
    geno = hillClimb.initGenotypes(hyperGeno)
    
    n = 50
    fitnesses = []
    for i in range(n):
        print('Iteration:',i+1,'out of',n)
        geno = hillClimb.nextGenotypes(hyperGeno, geno, problem)
        problem['rng'] = ecology.nextRng(problem['rng'])
        fitnesses.append(geno['fitness'])
    return fitnesses

def overnightHillClimb():
    timeForOnePattern = 0.087135306 # one rep, one pattern, assuming all cores are used.
    totalTime = 60*60*8
    safetyMargin = 0.8
    reps = 256
    n = round(safetyMargin*totalTime/timeForOnePattern/reps)
    
    # A long hillClimb, hopefully things improve.
    pool = taskMgr.getPool()
    hyperGeno = hillClimb.hyperGenotype(initDensity=0.50, mutateRate=0.005, moment=1, replicates=reps)
    problem = ecology.makeProblem()
    geno = hillClimb.initGenotypes(hyperGeno)
    
    fitnesses = []
    patterns = []
    t0 = time.time()
    for i in range(n):
        print('Iteration:',i+1,'out of',n,'starting time',time.time()-t0)
        geno = hillClimb.nextGenotypes(hyperGeno, geno, problem)
        problem['rng'] = ecology.nextRng(problem['rng'])
        fitnesses.append(geno['fitness'])
        patterns.append(geno['pattern'])
    return {"fitnesses":fitnesses,"patterns":patterns}

def randomPatternStatistics():
    # Fitness (furthest influence) for a random pattern.
    pool = taskMgr.getPool()
    nPatternsToAverage = 10
    nTrialsPerPattern = 1024
    density0 = 0.5 # anything reasonable enough that generates pretty good fitness.
    problem = ecology.makeProblem()
    problem['rng'] = ecology.newRng(122131)
    
    hyperGeno = hillClimb.hyperGenotype(initDensity=density0)
    hyperGeno['rng'] = ecology.newRng(1905232)
    
    geno = hillClimb.singleGenotype(hyperGeno)
    
    rightwardsRows = np.zeros((nPatternsToAverage, nTrialsPerPattern), dtype=np.float64)
    rightwardsAvgs = np.zeros((nPatternsToAverage, 1), dtype=np.float64)
    rightwardsSigmas = np.zeros((nPatternsToAverage, 1), dtype=np.float64)
    
    problems = list()
    patterns = list()
    for i in range(nPatternsToAverage):
        print('Iteration: ',i+1,'out of',nPatternsToAverage)
        (pattern, _) = genetics.oneToOne(geno, problem)
        patterns.append(pattern)
        problems.append(problems)
        rightwards_ = ecology.vectorBeforeVsAfter(problem, pattern, ecology.mostRightward, nTrialsPerPattern)
        rightwards = np.array(rightwards_, dtype=np.float64)
        rightwardsRows[i,:] = rightwards
        rightwardsAvgs[i,0] = np.mean(rightwards)
        rightwardsSigmas[i,0] = np.std(rightwards)
        
        #print("rightwards",rightwards,"mean: ",np.mean(rightwards), "sigma: ",np.std(rightwards))
        #print("rightwardsRows",rightwardsRows)
        
        
        geno['rng'] = ecology.nextRng(geno['rng'])
        problem['rng'] = ecology.nextRng(problem['rng'])
        
    print("Intra-pattern:",np.mean(rightwardsSigmas),"inter-pattern:",np.std(rightwardsAvgs))
    finiteErr = np.mean(rightwardsSigmas)/math.sqrt(nTrialsPerPattern)
    finiteErrErr = finiteErr/math.sqrt(nPatternsToAverage)
    print("WARNING: finite sample size will create about",max(0.1,finiteErr-2*finiteErrErr),'-', finiteErr+2*finiteErrErr,"of fake inter-pattern sigma.")
    return {"rightwardsRows":rightwardsRows,"rightwardsAvgs":rightwardsAvgs,"rightwardsSigmas":rightwardsSigmas,"problems":problems,"patterns":patterns}
        
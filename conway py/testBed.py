# self-contains test/demonstration functions.
import taskMgr
import hillClimb
import ecology
import genetics
import time
import math
import numpy as np

def nextyBANG(hyperGeno, problem, geno, salt):
    # super duper scramble. Salt should be different for each test.
    hyperGeno['seed'] = ecology.nextSeed(hyperGeno['seed'],salt+"h")
    problem['seed'] = ecology.nextSeed(problem['seed'],salt+"p")
    geno['seed'] = ecology.nextSeed(geno['seed'],salt+"s")

def testFitness():
    # Just gets the fitness of a single pattern.
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
    # Runs the hillclimber from a bad start, making it very easy to show improvement.
    # The pattern starts off very sparse and some new shapes tend to explode and improve the fitness.
    pool = taskMgr.getPool()
    hyperGeno = hillClimb.hyperGenotype(initDensity=0.01, mutateRate=0.04)
    problem = ecology.makeProblem()
    geno = hillClimb.initGenotypes(hyperGeno)
    
    nextyBANG(hyperGeno, problem, geno, 'testBed.hillClimbFromBadStart0')
    
    n = 50
    fitnesses = []
    for i in range(n):
        print('Iteration:',i+1,'out of',n)
        geno = hillClimb.nextGenotypes(hyperGeno, geno, problem)
        problem['seed'] = ecology.nextSeed(problem['seed'],'testBed.hillClimbFromBadStart')
        fitnesses.append(geno['fitness'])
    return fitnesses

def overnightHillClimb():
    # A long hill climb ran overnight from reasonable starting parameters.
    # This is hopefully the first non-trivial change.
    timeForOnePattern = 0.087135306 # one rep, one pattern, assuming all cores are used.
    totalTime = 60*60*8
    safetyMargin = 0.8
    
    # For poorly resolved signals and a linear landscape, the chance of improvement is ~ (#reps).
    # So it doesn't matter how many you do.
    # But for non-linear landscapes it's not the case, more is worse.
    # The landscape should be incredably non-linear.
    # Old value, marginaly resolved: reps = 256
    reps = 10000 # new value: well resolved only ~15% shift of sigma.
    n = round(safetyMargin*totalTime/timeForOnePattern/reps)
    
    # A long hillClimb, hopefully things improve.
    pool = taskMgr.getPool()
    hyperGeno = hillClimb.hyperGenotype(initDensity=0.50, mutateRate=0.01, replicates=reps)
    problem = ecology.makeProblem()
    geno = hillClimb.initGenotypes(hyperGeno)
    
    nextyBANG(hyperGeno, problem, geno, 'testBed.overnightHillClimb0')
    
    fitnesses = []
    patterns = []
    t0 = time.time()
    for i in range(n):
        print('Iteration:',i+1,'out of',n,'starting time',time.time()-t0)
        geno = hillClimb.nextGenotypes(hyperGeno, geno, problem)
        problem['seed'] = ecology.nextSeed(problem['seed'], 'testBed.overnightHillClimb')
        fitnesses.append(geno['fitness'])
        patterns.append(geno['pattern'])
    return {"fitnesses":fitnesses,"patterns":patterns}

def randomPatternStatistics():
    # The fitness of random patterns. Helps inform what the hill-climb params. 
    # History: make the overnightHillClimb, can't get it working.
    # Make this. TODO: tweak the overnight hill climb to fit.
    # June 24 2016 run:
    #Intra-pattern: 35.6449250635 inter-pattern: 2.68973276926
    #WARNING: finite sample size will create about 0.160882730965 - 0.42119645787 of fake inter-pattern sigma.
    pool = taskMgr.getPool()
    nPatternsToAverage = 20
    nTrialsPerPattern = 15000
    density0 = 0.5 # anything reasonable enough that generates pretty good fitness.
    problem = ecology.makeProblem()
    
    hyperGeno = hillClimb.hyperGenotype(initDensity=density0)
    
    geno = hillClimb.singleGenotype(hyperGeno)
    
    nextyBANG(hyperGeno, problem, geno, "testBed.randomPatternStatistics0")
    
    rightwardsRows = np.zeros((nPatternsToAverage, nTrialsPerPattern), dtype=np.float64)
    rightwardsAvgs = np.zeros((nPatternsToAverage, 1), dtype=np.float64)
    rightwardsSigmas = np.zeros((nPatternsToAverage, 1), dtype=np.float64)
    
    problems = list()
    patterns = list()
    for i in range(nPatternsToAverage):
        print('Pattern: ',i+1,'out of',nPatternsToAverage)
        pattern = genetics.oneToOne(geno, problem)
        patterns.append(pattern)
        problems.append(problems)
        rightwards_ = ecology.vectorBeforeVsAfter(problem, pattern, ecology.mostRightward, nTrialsPerPattern)
        rightwards = np.array(rightwards_, dtype=np.float64)
        rightwardsRows[i,:] = rightwards
        rightwardsAvgs[i,0] = np.mean(rightwards)
        rightwardsSigmas[i,0] = np.std(rightwards)
        
        #print("rightwards",rightwards,"mean: ",np.mean(rightwards), "sigma: ",np.std(rightwards))
        #print("rightwardsRows",rightwardsRows)
        
        geno['seed'] = ecology.nextSeed(geno['seed'], 'testBed.randomPatternDirection 0')
        problem['seed'] = ecology.nextSeed(problem['seed'], 'testBed.randomPatternDirection 1')
        
    print("Intra-pattern:",np.mean(rightwardsSigmas),"inter-pattern:",np.std(rightwardsAvgs))
    finiteErr = np.mean(rightwardsSigmas)/math.sqrt(nTrialsPerPattern)
    finiteErrErr = finiteErr/math.sqrt(nPatternsToAverage)
    print("WARNING: finite sample size will create about",max(0.1,finiteErr-2*finiteErrErr),'-', finiteErr+2*finiteErrErr,"of fake inter-pattern sigma.")
    return {"rightwardsRows":rightwardsRows,"rightwardsAvgs":rightwardsAvgs,"rightwardsSigmas":rightwardsSigmas,"problems":problems,"patterns":patterns}
  
  
def landscapeRuggedness():
    # Like randomPatternStatistics but measures the effect of tiny changes.
    pool = taskMgr.getPool()
    
    # at 120x144 there is still >80% chance of changing a pixel at        0.0001  (probably no pixels at 0.00001 however)
    # We got these values:
    #[ 2.51262083] for 0.1
    #[ 4.19366987]
    #[ 4.35736966]
    #[ 3.70952822]
    #[ 4.14147034]
    #[ 4.08993153]
    #[ 4.7715052 ]
    #[ 5.54144905]
    #[ 1.01437408]
    #[ 1.98068043]
    #[ 0.8983365 ] for 1e-5
    
    mus = [0.1, 0.05, 0.025, 0.01, 0.005, 0.0025, 0.001, 0.0005, 0.00025, 0.0001, 0.00001]
    nMu = len(mus)
    nTrialsPerPattern = 3000
    nMutationsPerMu = 5
    
    density0 = 0.5 # anything reasonable enough that generates pretty good fitness.
    problem = ecology.makeProblem()
    
    hyperGeno = hillClimb.hyperGenotype(initDensity=density0)
    
    geno = hillClimb.singleGenotype(hyperGeno)
    
    nextyBANG(hyperGeno, problem, geno, "testBed.landscapeRuggedness0")
    
    sigmas = np.zeros((nMu, 1), dtype=np.float64)
    
    for i in range(nMu):
        print('Pattern: ',i+1,'out of',nMu)
        delta = list()
        for j in range(nMutationsPerMu):
            #print("OK1")
            pattern0 = genetics.oneToOne(geno, problem)
            #print("OK2")
            rightwards_0 = ecology.vectorBeforeVsAfter(problem, pattern0, ecology.mostRightward, nTrialsPerPattern)
            #print("OK3")
            rightwards0 = np.mean(np.array(rightwards_0, dtype=np.float64))
            #print("OK4")
            pattern1 = genetics.pointwiseMutate(pattern0, geno['seed'], mus[i])
            #print("OK5")
            problem['seed'] = ecology.nextSeed(problem['seed'], 'testBed.landscapeRuggedness1')
            #print("OK6")
            rightwards_ = ecology.vectorBeforeVsAfter(problem, pattern1, ecology.mostRightward, nTrialsPerPattern)
            rightwards = np.mean(np.array(rightwards_, dtype=np.float64))
            #print("OK7")
            geno['seed'] = ecology.nextSeed(geno['seed'], 'testBed.landscapeRuggedness2')
            problem['seed'] = ecology.nextSeed(problem['seed'], 'testBed.landscapeRuggedness3')
            delta.append(rightwards0-rightwards)
            #print("OK8")
        sigmas[i] = np.std(np.array(delta, dtype=np.float64))
        
    print("Mus-pattern:",mus,"inter-pattern sigma:",sigmas)
    finiteErr = 35.6449250635/math.sqrt(nTrialsPerPattern) # intra-trial variance.
    print("Background noise is on the order of: ",finiteErr*1.414)
    return {"Mus":mus,"sigmas":sigmas}
        
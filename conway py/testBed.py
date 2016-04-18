# self-contains test/demonstration functions.
import taskMgr
import hillClimb
import ecology

def testFitness():
    hyper = hillClimb.hyperGenotype()
    geno = hillClimb.initGenotypes(hyper)
    problem = ecology.makeProblem()
    (pattern, _) = hillClimb.phenotype(geno, problem)
    n = 16
    score = ecology.fitness(problem, pattern, n)
    return score

#def hillClimbFromBadStart():
#    # Runs the hillclimber from a bad start, making it easier to show improvement.
#    pool = taskMgr.getPool()
#    climber = TODO

def sampleError():
    import traceback
    import sys
    try:
        testFitness()
    except:
        ex_type, ex, tb = sys.exc_info()
        stack = traceback.extract_tb(tb)
        print(stack[0].lineno)

"""
import testBed
pr(testBed.testFitness())

"""
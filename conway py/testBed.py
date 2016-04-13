# self-contains test/demonstration functions.
import taskMgr
import hillClimb
import ecology

def testFitness():
    pool = taskMgr.getPool()
    climber = hillClimb.makeClimber()
    problem = ecology.makeProblem()
    n = 16
    score = ecology.fitness(problem, paattern, n, pool)
    return score

#def hillClimbFromBadStart():
#    # Runs the hillclimber from a bad start, making it easier to show improvement.
#    pool = taskMgr.getPool()
#    climber = TODO
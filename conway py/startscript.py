# A list of commands that will automatically be ran when we startup.
# This shouldn't do the "heavy lifting" of programming, rather it is a convenience
# if you are having ot enter many things into the command line at once.

# old tests:
def testMakePatterns():
    x = []
    x.append('import testBed')
    x.append('r = testBed.testFitness()')
    x.append('fitness = r["result"]')
    x.append('gui = r["gui"]')
    x.append('plotQ.put(gui)')
    return x

def testHillClimb0(): # from a purposefully bad start.
    x = []
    x.append('import testBed')
    x.append('import graph')
    x.append('fitnesses = testBed.hillClimbFromBadStart()')
    x.append('cmds = graph.clearFigure()')
    x.append('plotQ.put(cmds)')
    x.append('cmds = graph.linePlot(None, fitnesses, "time", "fitness", "From a bad start")')
    x.append('plotQ.put(cmds)')
    return x

def testHillClimbOvernight(): # from an OK start, ran overnight.
    x = []
    x.append('import testBed')
    x.append('import graph')
    x.append('result = testBed.overnightHillClimb()')
    x.append('fitnesses = result["fitnesses"]')
    x.append('cmds = graph.clearFigure()')
    x.append('plotQ.put(cmds)')
    x.append('cmds = graph.linePlot(None, fitnesses, "time", "fitness", "The first real hopefully-uphill climb.")')
    x.append('plotQ.put(cmds)')
    return x

def testRandomPatternStatistics():
    x = []
    x.append('import testBed')
    x.append('import graph')
    x.append('result = testBed.randomPatternStatistics()')
    return x

def testRugged():
    x = []
    x.append('import testBed')
    x.append('import graph')
    x.append('result = testBed.landscapeRuggedness()')
    return x

def cmds():
    #x = testMakePatterns()
    #x = testHillClimb0()
    #x = testHillClimbOvernight()
    #x = testRandomPatternStatistics()
    x = testRugged()
    return x
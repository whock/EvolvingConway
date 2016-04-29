# A list of commands that will automatically be ran when we startup.
# This shouldn't do the "heavy lifting" of programming, rather it is a convenience
# if you are having ot enter many things into the command line at once.
def cmds():
    x = []
    x.append('import testBed')
    x.append('r = testBed.testFitness()')
    x.append('fitness = r["result"]')
    x.append('gui = r["gui"]')
    x.append('doGuiCmd(gui)')
    return x
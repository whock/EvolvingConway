# Parallel mapping tool that gets around issues with pickle.
import concurrent.futures

# fn(a,b,c,d)
# pmap.maplist(pool, fn, a, b, c, d) ; maps fn over anything that is a list.

__salt = 'vghytrdx3248390~?"cvbhytre'

pool = concurrent.futures.ProcessPoolExecutor() #or use a ThreadPoolExecutor. Optional max_workers=xyz

def box(ls):
    # Boxes a list so that maplist treats it as a constant rather than mapping each element of it.
    # (You can also pass non-lists here, if you don't know if it is a list).
    return {'obj': ls, 'salt': __salt}

def unboxIfBoxed(x):
    # unboxes if we boxed it. Otherwise leaves it alone.
    if isinstance(x, dict) and ('obj' in x) and ('salt' in x) and x['salt'] == __salt:
        return x['obj']
    else:
        return x

def applyFn(fnAndArgArray): # Splats the argument array, returns an error msg because it's in a try-catch..
    try:
        #print("Taking a RUN.")
        fn = fnAndArgArray[0] # the fn is first.
        argArray = fnAndArgArray[1:]
        return fn(*argArray)
    except:
        #print("Error arrrorererere.")
        ex_type, ex, tb = sys.exc_info()
        #print("Error in the function used for pool.map()")
        return {"type": ex_type, "eceptionx": ex, "trace": tb}
    return fn(*argArray)

def dumbTestMap(x):
    return x

def maplist(fn, *fnargs):
    # Maps fn across *fnargs.
    # *fnargs that are a list are mapped across, but
    # *fnargs that aren't a list are held constant..
    # If you want a list to be a constant, box it with the box() command.
    #  1-element-long lists are held constant.
    # Replicate the constants:
    fnar = list(fnargs)
    n = 1e100 # The number of (embarrassingly parellel) iterations is the minimum array.
    nArg = len(fnar)
    for i in range(nArg):
        fa = fnar[i]
        if isinstance(fa, list):
            n = min(n, len(fa))
    if n==1e100: # no lists, so length 1:
        n = 1
    
    listOfArgLists = list()
    for i in range(nArg):
        fa = unboxIfBoxed(fnar[i])
        if not isinstance(fa, list):
            fa1 = list()
            for j in range(n): # scalar => vector.
                fa1.append(fa)
            fa = fa1
        listOfArgLists.append(fa)
    
    argsEachIter = list() # each element can go to a separate processor.
    for i in range(n): # transpose code.
        iterI = [fn] # the function is first. 
        for j in range(nArg):
            iterI.append(listOfArgLists[j][i])
        argsEachIter.append(iterI)
    
    
    #print("about to map: ", fn, 'WITH: ', n, "iterations")
    #return pool.map(dumbTestMap, range(10))
    #print("DONE")
    return list(pool.map(applyFn, argsEachIter))

def shutdown():
    pool.shutdown()
# Parallel mapping tool that gets around issues with pickle.

# fn(a,b,c,d)
# pmap.maplist(pool, fn, a, b, c, d) ; maps fn over anything that is a list.

__salt = 'vghytrdx3248390~?"cvbhytre'

def box(ls):
    # Boxes a list so that maplist treats it as a constant rather than mapping each element of it.
    return {'obj': ls, 'salt': __salt}

def unboxIfBoxed(x):
    # unboxes if we boxed it. Otherwise leaves it alone.
    if isinstance(x, dict) and ('obj' in x) and ('salt' in x) and x['salt'] == __salt:
        return x['obj']
    else:
        return x

def maplist(pool, fn, *fnargs):
    # Maps fn across *fnargs.
    # *fnargs that are a list are mapped across, but
    # *fnargs that aren't a list are held constant..
    # If you want a list to be a constant, box it with the box() command.
    #  1-element-long lists are held constant.
    # Replicate the constants:
    fnar = list(*fnargs)
    # Calculate n (the smallest >1 length list):
    n = 1e100 
    for i in range(len(fnar)):
        fa = fnar[i]
        if isinstance(fa, list):
            n = min(n, len(fa))
    if n==1e100: # no lists, so length 1:
        n = 1
    
    fnarv = list() # vectorized form (shallow copy the non-vectors, unboxing and copy of singleton vectors).
    for i in range(len(fnar)):
        fa = unboxIfBoxed(fnar[i])
        fnarvi = list()
        if isinstance(fa, list): # criteria to use as-is.
            for j in range(n):
                fnarvi.append(fa[0]) # unbox the singleton list.
        else:
            for j in range(n):
                fnarvi.append(fa)
        fnarv.append(fnarvi)
    return pool.map(fn, *fnarv)
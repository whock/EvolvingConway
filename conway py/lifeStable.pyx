# Stable version: should be relativly reliable.
#                          (perf vs safety)                    (perf vs safety)
#!python
#cython: language_level=3, boundscheck=True, wraparound=False, initializedcheck=True, cdivision=True

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
cimport cython
from libc.math cimport round, ceil

################################################
# Basic how to:
# Use cdef int, cdef float, cdef char*, etc for all varaibles that are c typed (except function args).
#   Also do it to the "i" in "for i in range(...)" loops, etc.
#   Use object for Python structures.
#   Use def for functions you call from python, but reamamber: each call to def is slow.
#       Use cpdef if you are callind functions from inner loops and python.
#
# Use libc.math for native math.
#
# Common errors, how to debug them, and why they occur:
# "cdef statement not allowed here"
#     Don't define variables inside loops, etc. Only at the root of the class or functions.
#     Python variables defined ina loop are useable outside of said loop, but not for C.
#     These two different systems are incompatable.
#  "Cannot convert 'xyzyx' to Python object"
#     cdef xyz ex
#     x = 1; # woops spelled ex wrong!
#     Python thinks x is you defining a new variable,
#     which is a python variable since there is no cdef type info.
#     But c and python don't interconvert for free.
#  The file is HUGE (slow probably as well) and has lots as __Pyx_PyObject_ calls, __Pyx_GOTREF, etc.
#    Did you cdef all types, ESPICALLY LOOP INDEXES (loop indexes don't throw an error)?
#    Do you use a self.variable that is not defined (look for where this mob of calls is)?
#    Did you disable bounds and wrap checking? (Relativly less important, but nested arrays take a big hit b/c where are lengths stored?).
#    Are you using python's math instead of libc.math?
#    A factor of 10 or so is normal (all the comments and longer variable names), plus 500 lines beginning and 1500 lines at end.
#    Case study this file: 8000 lines -> 4000 lines and about 7 times faster compile!
#  Bounds checks not working on arrays:
#    Use numpy arrays (more syntax and may be slower due to overhead).
#    Do what the C coders are doing.
################################################

################################################
# Writing and debugging (chunks with static chunks disabled):
# About 5 hours to write initial code (no oascilator detection).
#
# Debug phase 1 (3 hours): Making sure that it is using antive code and not sneaking in python objects.
#     This also removed run-time AttributeErrors.
#
# Debug phase 2 (2 hours): Make sure it is right for a single chunk.
#     Why did it segfault when all the safeties are enabled?
#       Oh, they don't be smart and store the lenght of an array (i.e. as the first element(s) and shift all your indexes up one).
#       Special feature: memory errors can cause segfaults at the termination of the program.
#     Side effect: helps discover errors involving more than one chunk.
#
# Debug phase 3 (2 hours): multible chunks.
#   Some simple array errors, looking at the pattern animate is good enough.
#   Varying parameters widely helped detect harder-to-find bugs.
#
# Debug phase 4 (15 min): does the optimization for static chunks work:
#   This is very, very short!
################################################

# classes can handle thier own destructors.
cdef class Life:
   
    # the spaceship travells in the + X direction, dead boundary conditions.
    # For now the y has wrap-around boundary conditions.
   
    # The field is broken into chunks that are individually on or off depending whether
    # there is any active pattern in the region vs stable (short-period oscilations are also covered).
    # total size = (chunkDiam * chunksX, chunkDiam * chunksY).
    
    cdef int** state # current state. Note: The optimization algoryhtim does not save memory.
    cdef int** nextstate # temp buffer for the next cell state, alive or dead.
        # note: unwrapped as per matlab arrays.
    cdef int* active # whether each cell is active, and if active how much it is active.
    cdef int* nextActive # a buffer.
    
    # sizes set when the class if built:
    cdef int chunkDiam # size per chunk.
    cdef int chunksX # number of chunks.
    cdef int chunksY
    
    ########################## Debug functions ##########################
    @cython.boundscheck(True)
    def makeMemoryError(self):
        cdef int * xyz
        cdef int out
        xyz = <int*> PyMem_Malloc(10*sizeof(int*))
        out = xyz[100000000] # bounds check doesn't check the arrays.
        return out
    
    def chunkerBoard(self):
        # chunk colored in a chechkboard pattern.
        cdef size_t i
        cdef int cx
        cdef int cy
        out = []
        for i in range(self.chunkDiam*self.chunksX):
            out.append([])
            for j in range(self.chunkDiam*self.chunksY):
                cx = i/self.chunkDiam
                cy = j/self.chunkDiam

                out[i].append((cx+cy)%2)
        return out

    def chunkerBoard(self):
        # chunk colored in a chechkboard pattern.
        cdef size_t i
        cdef int cx
        cdef int cy
        out = []
        for i in range(self.chunkDiam*self.chunksX):
            out.append([])
            for j in range(self.chunkDiam*self.chunksY):
                cx = i/self.chunkDiam
                cy = j/self.chunkDiam
                
                out[i].append((cx+cy)%2)
        return out

    def activeBoard(self):
        # chunk colored by how active it is.
        cdef size_t i
        cdef int cx
        cdef int cy
        out = []
        for i in range(self.chunkDiam*self.chunksX):
            out.append([])
            for j in range(self.chunkDiam*self.chunksY):
                cx = i/self.chunkDiam
                cy = j/self.chunkDiam
                
                
                out[i].append(self.active[cy + self.chunksY*cx])
        return out

    ########################## Memory managment functions #########################
    cdef allocateMemory(self, size_t _chunkDiam, size_t _chunksX, size_t _chunksY):
        cdef size_t i
        
        self.chunksX = _chunksX
        self.chunksY = _chunksY
        self.chunkDiam = _chunkDiam
        cdef int numChunk = _chunksX*_chunksY
        cdef int numPerChunk = _chunkDiam*_chunkDiam
        self.state = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.nextstate = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        
        for i in range(numChunk):
            self.state[i] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            self.nextstate[i] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))

        self.active = <int*> PyMem_Malloc(numChunk*sizeof(int))
        self.nextActive = <int*> PyMem_Malloc(numChunk*sizeof(int))
            
    #def __cinit__(self):
    cdef freeMemory(self): # this MUST be a cdef
        cdef size_t i
        
        PyMem_Free(self.active)
        PyMem_Free(self.nextActive)
        for i in range(self.chunksX*self.chunksY):
            PyMem_Free(self.state[i])
            PyMem_Free(self.nextstate[i])
        PyMem_Free(self.state)
        PyMem_Free(self.nextstate)

    def __dealloc__(self): # called when python GC's an instance of this class.
        self.freeMemory()

    ########################## User interaction ##########################
    def setPattern(self, object listOfLists):
        self.setPatternAndChunk(listOfLists, 16)

    def setPatternAndChunk(self, object listOfLists, int chunkDiam):
        cdef int whichChunkX
        cdef int whereInChunkX
        cdef int whichChunkY
        cdef int whereInChunkY
        cdef int cell
        cdef size_t i
        cdef size_t j
        
        # Sets a pattern, padding on the bottom if the size is not an even multible (chunkDiam * chunksY = height).
        # listOfList is a list of COLUMNS.
        cdef int widthSmall = len(listOfLists)
        cdef int heightSmall = len(listOfLists[0])
        self.chunksX = (widthSmall-1)/chunkDiam+1
        self.chunksY = (heightSmall-1)/chunkDiam+1
        self.allocateMemory(chunkDiam, self.chunksX, self.chunksY)
        
        # make sure everything is zero (as we zero-pad):
        for i in range(self.chunksX*self.chunksY):
            for j in range(chunkDiam*chunkDiam):
                self.state[i][j] = 0
        
        for i in range(widthSmall):
            col = listOfLists[i]
            whichChunkX = int(i/chunkDiam);
            whereInChunkX = i - whichChunkX*chunkDiam
            for j in range(heightSmall):
                whichChunkY = int(j/chunkDiam);
                whereInChunkY = j - whichChunkY*chunkDiam
                cell = col[j] # this pixel's value.
                self.state[whichChunkY + self.chunksY*whichChunkX][whereInChunkY + chunkDiam*whereInChunkX] = cell

        for i in range(self.chunksX*self.chunksY):
            self.active[i] = 1 # turn on activity initially at least.

            # No need to set the nextstate and nextActive buffers as their value does not depend on the timestep.

    def getPattern(self):
        cdef int whichChunkX
        cdef int whereInChunkX
        cdef int whichChunkY
        cdef int whereInChunkY
        cdef int cell
        cdef int width = self.chunksX*self.chunkDiam
        cdef int height = self.chunksY*self.chunkDiam
        cdef size_t i
        cdef size_t j
        
        # returns a list of COLUMNS.
        out = []
        for i in range(width):
            col = []
            out.append(col)
            whichChunkX = int(i/self.chunkDiam);
            whereInChunkX = i - whichChunkX*self.chunkDiam
            for j in range(height):
                whichChunkY = int(j/self.chunkDiam);
                whereInChunkY = j - whichChunkY*self.chunkDiam
                cell = self.state[whichChunkY + self.chunksY*whichChunkX][whereInChunkY + self.chunkDiam*whereInChunkX] # this pixel's value.
                col.append(cell)
        return out

    ########################## The algorythim itself ##########################
    def step(self):
        # single step of conways life.
        cdef int numChunk = self.chunksX*self.chunksY
        cdef int numPerChunk = self.chunkDiam*self.chunkDiam
        cdef int diam = self.chunkDiam
        cdef int * st
        cdef int * nextst
        cdef int edge
        cdef int sege
        cdef int above
        cdef int below
        cdef int * chunk
        cdef int northChanged
        cdef int southChanged
        cdef int eastChanged
        cdef int westChanged
        cdef size_t i
        cdef size_t j
        cdef size_t k
        cdef size_t ii
        cdef size_t jj
        # Set nextstate to the number of neighbors-alive:
        for i in range(numChunk): # Intra-chunk contribution to number of neighbors.
            # for each pixel we count up it's neighbors' states.
            # Note: Also implicitly sets the chunk to zero b4 summing the neighbors.
            if self.active[i] > 0:
                st = self.state[i]
                nextst = self.nextstate[i]
                #for j in range(0, diam*diam): # TODO: is this extra reset nessesary?
                #   nextst[j] = 0
                for j in range(1,diam-1): # Excluding the edge border of the chunk.
                    for k in range(1, diam-1):
                        nextst[j+ k*diam] = st[j-1+k*diam] + st[j+1+k*diam] + st[j+(k-1)*diam] + st[j+(k+1)*diam] # ortho
                        nextst[j+ k*diam] += st[j-1+(k-1)*diam] + st[j+1+(k+1)*diam] + st[j+1+(k-1)*diam] + st[j-1+(k+1)*diam] # diag.
                for j in range(1,diam-1): # the left and right columns
                    nextst[j] = st[j-1] + st[j+1] + st[j-1 + diam] + st[j+1 + diam] + st[j + diam]
                    edge = (diam-1)*diam
                    sege = (diam-2)*diam # Second to eDGE.
                    nextst[j + edge] = st[j-1+edge] + st[j+1+edge] + st[j-1 + sege] + st[j+1 + sege] + st[j + sege]
                for j in range(1,diam-1): # the top and bottom rows.
                    nextst[diam*j] = st[diam*j-diam] + st[diam*j+diam] + st[diam*j + 1] + st[diam*j-diam+1] + st[diam*j+diam+1]
                    nextst[diam*j+diam-1] =st[diam*j-2]+st[diam*j+diam-2]+st[diam*j+2*diam-2]+st[diam*j-1]+st[diam*j+2*diam-1]
                # the corners:
                if diam>1:
                    nextst[0] = st[1] + st[diam] + st[diam + 1]
                    nextst[diam-1] = st[diam-2] + st[2*diam-1] + st[2*diam-2]
                    nextst[diam*(diam-1)] = st[diam*(diam-1)+1] + st[diam*(diam-2)] + st[diam*(diam-2)+1]
                    nextst[diam*diam-1] = st[diam*diam-2] + st[diam*(diam-1)-1] + st[diam*(diam-1)-2]
                else:
                    nextst[0] = 0
        for i in range(self.chunksY): # Inter-chunk contribution to number of neighbors of our chunk.
            above = (i-1+self.chunksY) % self.chunksY # wrap-around.
            below = (i+1)              % self.chunksY #wrap around.
            for j in range(self.chunksX):
                if self.active[i + self.chunksY*j] > 0:
                    st = self.state[i + self.chunksY*j] # state.
                    nextst = self.nextstate[i + self.chunksY*j]
                    if j>0:
                        # The chunk to the left of us:
                        chunk = self.state[i + self.chunksY*(j - 1)]
                        for ii in range(1, diam-1):
                            nextst[ii] += chunk[diam*(diam-1)+ii] + chunk[diam*(diam-1)+ii - 1] + chunk[diam*(diam-1)+ii + 1]
                        nextst[0] += chunk[diam*(diam-1)] + chunk[diam*(diam-1) + 1]
                        if diam>1:
                            nextst[diam-1] += chunk[diam*diam-2] + chunk[diam*diam-1]
                
                        # The chunk northwest of us:
                        nextst[0] += self.state[above + self.chunksY*(j - 1)][diam*diam - 1]

                        # The chunk southwest of us:
                        nextst[diam-1] += self.state[below + self.chunksY*(j - 1)][diam*(diam-1)]
                
                    if j<self.chunksX-1:
                        # The chunk to the right of us:
                        chunk = self.state[i + self.chunksY*(j + 1)]
                        for ii in range(1, diam-1):
                            nextst[ii + diam*(diam-1)] += chunk[ii] + chunk[ii-1] + chunk[ii+1]
                        nextst[diam*(diam-1)] += chunk[0] + chunk[1]
                        if diam>1:
                            nextst[diam*diam-1] += chunk[diam-2] + chunk[diam-1]
                
                        # The chunk northeast of us:
                        nextst[diam*(diam-1)] += self.state[above + self.chunksY*(j + 1)][diam-1]

                        # The chunk southeast of us:
                        nextst[diam*diam - 1] += self.state[below + self.chunksY*(j + 1)][0]

                    # The chunk above us:
                    chunk = self.state[above + self.chunksY*j]
                    for ii in range(1, diam-1):
                        nextst[diam*ii] += chunk[diam*ii + diam - 1] + chunk[diam*ii + 2*diam - 1] + chunk[diam*ii - 1]
                    nextst[0] += chunk[diam - 1] + chunk[2*diam - 1]
                    if diam>1:
                        nextst[diam*(diam-1)] += chunk[diam*diam - 1] + chunk[diam*(diam -1) - 1]
                    
                    # The chunk below us:
                    chunk = self.state[below + self.chunksY*j]
                    for ii in range(1, diam-1):
                        nextst[diam*ii + diam - 1] += chunk[diam*ii - diam] + chunk[diam*ii] + chunk[diam*ii + diam]
                    nextst[diam - 1] += chunk[0] + chunk[diam]
                    if diam>1:
                        nextst[diam*diam - 1] += chunk[diam*(diam-1)] + chunk[diam*(diam-2)]

        cdef int timeOut = 16 # Timeout for the chunk.
        # Use the current state and conways rules to set the new state:
        for i in range(numChunk):
            if self.active[i] > 0:
                st = self.state[i]
                nextst = self.nextstate[i]
                for k in range(diam*diam):
                    if st[k]>0: # survive on 2/3
                        if nextst[k] == 2 or nextst[k] == 3: # nextst temporaly was holding the live-neighbor count.
                            nextst[k] = 1
                        else:
                            nextst[k] = 0
                    else: # birth on 3
                        if nextst[k] == 3: # nextst temporaly was holding the live-neighbor count.
                            nextst[k] = 1
                        else:
                            nextst[k] = 0
        # Re-activate deactivated chunks if they are bordering an active chunk and the active chunk has changed:
        for i in range(numChunk): # this copying step is nessessary.
            self.nextActive[i] = self.active[i]
        for i in range(self.chunksY):
            for j in range(self.chunksX):
                if self.active[i + self.chunksY*j] > 0:
                    st = self.state[i + self.chunksY*j]
                    nextst = self.nextstate[i + self.chunksY*j]
                    
                    above = (i-1+self.chunksY) % self.chunksY # wrap-around.
                    below = (i+1)              % self.chunksY #wrap around.
                    
                    # check if borders have changed:
                    northChanged = 0
                    southChanged = 0
                    eastChanged = 0
                    westChanged = 0
                    for jj in range(0, diam):
                        if st[jj*diam] != nextst[jj*diam]:
                            northChanged = 1
                        if st[jj*diam+diam-1] != nextst[jj*diam+diam-1]:
                            southChanged = 1
                        if st[jj] != nextst[jj]:
                            eastChanged = 1
                        if st[jj+diam*(diam-1)] != nextst[jj+diam*(diam-1)]:
                            westChanged = 1
                    
                    # use changing borders to update the neighbors:
                    if northChanged > 0:
                        self.nextActive[above + self.chunksY*j] = timeOut
                        if j>0:
                            self.nextActive[above + self.chunksY*(j-1)] = timeOut
                        if j<self.chunksX - 1:
                            self.nextActive[above + self.chunksY*(j+1)] = timeOut
                    if southChanged > 0:
                        self.nextActive[below + self.chunksY*j] = timeOut
                        if j>0:
                            self.nextActive[below + self.chunksY*(j-1)] = timeOut
                        if j<self.chunksX - 1:
                            self.nextActive[below + self.chunksY*(j+1)] = timeOut
                    if eastChanged > 0 and j>0:
                        self.nextActive[below + self.chunksY*(j-1)] = timeOut
                        self.nextActive[i + self.chunksY*(j-1)] = timeOut
                        self.nextActive[above + self.chunksY*(j-1)] = timeOut
                    if westChanged > 0 and j<self.chunksX - 1:
                        self.nextActive[below + self.chunksY*(j+1)] = timeOut
                        self.nextActive[i + self.chunksY*(j+1)] = timeOut
                        self.nextActive[above + self.chunksY*(j+1)] = timeOut
        for i in range(numChunk):
            self.active[i] = self.nextActive[i]
        # Deactivate chunks that don't change:
        for i in range(numChunk):
            if self.active[i] == 1: # about to deactivate check.
                st = self.state[i]
                nextst = self.nextstate[i]
                change = 0
                for k in range(diam*diam):
                    if st[k] != nextst[k]:
                        change = 1
                if change==0:
                    self.active[i] == 0
                else:
                    self.active[i] = timeOut
            elif self.active[i] > 0:
                self.active[i] -= 1 # time to activation check.
        # Set state to next state:
        for i in range(numChunk):
            if self.active[i] > 0:
                st = self.state[i]
                nextst = self.nextstate[i]
                for k in range(diam*diam):
                    st[k] = nextst[k]


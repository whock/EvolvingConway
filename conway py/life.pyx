#                          (perf vs safety)                    (perf vs safety)
#!python
#cython: language_level=3, boundscheck=True, wraparound=False, initializedcheck=True, cdivision=True

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
cimport cython
from libc.math cimport round, ceil
import numpy as np
cimport numpy as np

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
#    cython life.pyx -a is useful to see where python interaciton is.
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
#
# Coding phase 2A: Short-period oscillation optimization.
#   1 hr thinking. 1 hr core coding. 1.5 hour debugging.
#       refactoring added an extra hour, not including debugging.
# Coding phase 2B: Numpy.
#   About 2 hr and 0.5 hr debugging, most fo the time learning numpy in the first place.
#
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
    cdef int* active # 1 = active. -globalPeriod = inactive. >-globalPeriod>=0 is the countdown (see below).
    
    # sizes set when the class if built:
    cdef int chunkDiam # size per chunk.
    cdef int chunksX # number of chunks.
    cdef int chunksY
    
    ## Oscellation stuff:
    cdef unsigned int time # current time in the simultion, increases by one at the end of each step. Overflows/wraparounds don't cause problems.
    cdef int globalPeriod # The period for which we check for oscilations.
                            # This must be <= the chunk size, and should be a highly composite number like 12 for a 16x16 chunk.

    cdef int** referenceState # The reference state used for oscilation checks. Set to state every globalPeriod steps.
    
    # Extracting the pattern at intermediate times means that we must
    cdef int** patternOutputBuffer # Temp for running patterns.
    cdef int** patternOutputBuffer1 # Temp for running patterns.
    
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
        cdef size_t I
        cdef size_t J
        cdef int height = self.chunkDiam*self.chunksY
        cdef int width = self.chunkDiam*self.chunksX
        cdef np.ndarray [np.int_t, ndim=2] out = np.zeros([height, width], dtype=np.int)
        for I in range(height):
            for J in range(width):
                out[I,J] = (I/self.chunkDiam+J/self.chunkDiam)%2
        return out

    def activeBoard(self):
        # chunk colored by how active it is.
        cdef size_t I
        cdef size_t J
        cdef int height = self.chunkDiam*self.chunksY
        cdef int width = self.chunkDiam*self.chunksX
        cdef np.ndarray [np.int_t, ndim=2] out = np.zeros([height, width], dtype=np.int)
        for I in range(height):
            for J in range(width):
                out[I,J] = (self.active[I/self.chunkDiam + self.chunksY*(J/self.chunkDiam)])
        return out

    ########################## Memory managment functions #########################
    cdef int getPeriod(self, int chunkWidth):
        # A nice period that fits as a multible.
        cdef int out = 1
        
        if chunkWidth>=2: # keystone number (2)
            out = 2
        if chunkWidth>=4:
            out = 4
        if chunkWidth>=6: # keystone number (3)
            out = 6
        if chunkWidth>=12: # keystone number (2)
            out = 12
        if chunkWidth>=24:
            out = 24
        if chunkWidth>=48:
            out = 48
        if chunkWidth>=60: # keystone number (5)
            out = 60
        if chunkWidth>=120:
            out = 120
        if chunkWidth>=240:
            out = 240
        if chunkWidth>=420: # keystone number (7)
            out = 420
        return out

    cdef void allocateMemory(self, size_t _chunkDiam, size_t _chunksX, size_t _chunksY):
        cdef size_t u
        cdef size_t uu
        
        self.time = 0
        self.chunksX = _chunksX
        self.chunksY = _chunksY
        self.chunkDiam = _chunkDiam
        self.globalPeriod = self.getPeriod(self.chunkDiam)
        cdef int numChunk = _chunksX*_chunksY
        cdef int numPerChunk = _chunkDiam*_chunkDiam
        self.state = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.nextstate = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.referenceState = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.patternOutputBuffer = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.patternOutputBuffer1 = <int**> PyMem_Malloc(numChunk*sizeof(int*))
        self.active = <int*> PyMem_Malloc(numChunk*sizeof(int))
        
        for u in range(numChunk):
            self.state[u] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            self.nextstate[u] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            self.referenceState[u] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            self.patternOutputBuffer[u] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            self.patternOutputBuffer1[u] = <int*> PyMem_Malloc(numPerChunk*sizeof(int))
            
            for uu in range(numPerChunk): # clear the reference.
                self.referenceState[u][uu] = 0
            
    #def __cinit__(self):
    cdef void freeMemory(self): # this MUST be a cdef
        cdef size_t i
        
        for i in range(self.chunksX*self.chunksY):
            PyMem_Free(self.state[i])
            PyMem_Free(self.nextstate[i])
            PyMem_Free(self.referenceState[i])
            PyMem_Free(self.patternOutputBuffer[i])
            PyMem_Free(self.patternOutputBuffer1[i])
        PyMem_Free(self.state)
        PyMem_Free(self.nextstate)
        PyMem_Free(self.referenceState)
        PyMem_Free(self.patternOutputBuffer)
        PyMem_Free(self.patternOutputBuffer1)
        PyMem_Free(self.active)

    def __dealloc__(self): # called when python GC's an instance of this class.
        self.freeMemory()

    ########################## User interaction ##########################
    def setPattern(self, object listOfLists):
        self.setPatternAndChunk(listOfLists, 16)

    def setPatternAndChunk(self, np.ndarray[np.int_t, ndim=2] cells, int chunkDiam):
        cdef int whichChunkX
        cdef int whereInChunkX
        cdef int whichChunkY
        cdef int whereInChunkY
        cdef int cell
        cdef size_t i
        cdef size_t j
        
        # Sets a pattern, padding on the bottom if the size is not an even multible (chunkDiam * chunksY = height).
        # listOfList is a list of COLUMNS.
        cdef int widthSmall = cells.shape[0]
        cdef int heightSmall = cells.shape[1]
        self.chunksX = (widthSmall-1)/chunkDiam+1
        self.chunksY = (heightSmall-1)/chunkDiam+1
        self.allocateMemory(chunkDiam, self.chunksX, self.chunksY)
        
        # make sure everything is zero (in case the chunkDiam is not a factor of the input array size):
        for i in range(self.chunksX*self.chunksY):
            for j in range(chunkDiam*chunkDiam):
                self.state[i][j] = 0
        
        for i in range(widthSmall):
            whichChunkX = int(i/chunkDiam);
            whereInChunkX = i - whichChunkX*chunkDiam
            for j in range(heightSmall):
                whichChunkY = int(j/chunkDiam);
                whereInChunkY = j - whichChunkY*chunkDiam
                cell = cells[i,j] # this pixel's value.
                self.state[whichChunkY + self.chunksY*whichChunkX][whereInChunkY + chunkDiam*whereInChunkX] = cell

        for i in range(self.chunksX*self.chunksY):
            self.active[i] = 3 # turn on activity to full (non-periodic) initially at least.

            # No need to set the nextstate and nextActive buffers as their value does not depend on the timestep.

        # reset time so we don't get any suprises:
        self.time = 0

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
        cdef size_t I
        cdef size_t J
        cdef size_t u
        cdef size_t o
        cdef size_t uu
        
        # Dealing with periodicity in chunks:
        cdef int numStepToDo = self.time % self.globalPeriod
        # Note: active = 1 chunks are corrupt and active = 0 are out of date.
        # Set active < 3 chunks to the reference and run them numStepToDo.
            # Active = 0 and 1 are now accurate, but active = 2 are corrupt.
        # Then set active > 1 chunks to the current so 2 and 3 are correct.
        for u in range(self.chunksX*self.chunksY): # run step.
            if self.active[u]<3:
                for uu in range(self.chunkDiam*self.chunkDiam):
                    self.patternOutputBuffer[u][uu] = self.referenceState[u][uu]
        for o in range(numStepToDo):
            for i in range(self.chunksY):
                for j in range(self.chunksX):
                    if self.active[i + self.chunksY*j] < 3:
                        self.neighborcount(self.patternOutputBuffer1, self.patternOutputBuffer, j,i)
            for i in range(self.chunksY):
                for j in range(self.chunksX):
                    if self.active[i + self.chunksY*j] < 3:
                        self.stateUpdate(self.patternOutputBuffer, self.patternOutputBuffer1, j,i)
        for u in range(self.chunksX*self.chunksY):
            if self.active[u]>1:
                for uu in range(self.chunkDiam*self.chunkDiam):
                    self.patternOutputBuffer[u][uu] = self.state[u][uu]

        cdef np.ndarray [np.int_t, ndim=2] out = np.zeros([width, height], dtype=np.int)
        for I in range(height):
            whichChunkY = I/self.chunkDiam;
            whereInChunkY = I - whichChunkY*self.chunkDiam
            for J in range(width):
                whichChunkX = J/self.chunkDiam;
                whereInChunkX = J - whichChunkX*self.chunkDiam
                cell = self.patternOutputBuffer[whichChunkY + self.chunksY*whichChunkX][whereInChunkY + self.chunkDiam*whereInChunkX] # this pixel's value.
                out[J,I] = cell
        return out

    ########################## The algorythim itself ##########################
    cdef void neighborcount(self, int ** neighbors, int ** state, int xChunk, int yChunk):
        # neighbor count of the given chunk (included neighboring chunks).
        ##### Intra-chunk contribution to number of neighbors:
        cdef int chunkID = self.chunksY*xChunk + yChunk
        cdef int * st = state[chunkID]
        cdef int * nei = neighbors[chunkID]
        cdef size_t ii
        cdef size_t jj
        cdef size_t edge
        cdef size_t sege
        cdef int numChunk = self.chunksX*self.chunksY
        cdef int numPerChunk = self.chunkDiam*self.chunkDiam
        cdef int diam = self.chunkDiam
        cdef int * chunk
        cdef int above
        cdef int below
        
        for ii in range(1,diam-1): # Excluding the edge border of the chunk.
            for jj in range(1, diam-1):
                nei[ii+ jj*diam] = st[ii-1+jj*diam] + st[ii+1+jj*diam] + st[ii+(jj-1)*diam] + st[ii+(jj+1)*diam] # ortho
                nei[ii+ jj*diam] += st[ii-1+(jj-1)*diam] + st[ii+1+(jj+1)*diam] + st[ii+1+(jj-1)*diam] + st[ii-1+(jj+1)*diam] # diag.
        for ii in range(1,diam-1): # the left and right columns
            nei[ii] = st[ii-1] + st[ii+1] + st[ii-1 + diam] + st[ii+1 + diam] + st[ii + diam]
            edge = (diam-1)*diam
            sege = (diam-2)*diam # Second to eDGE.
            nei[ii + edge] = st[ii-1+edge] + st[ii+1+edge] + st[ii-1 + sege] + st[ii+1 + sege] + st[ii + sege]
        for jj in range(1,diam-1): # the top and bottom rows.
            nei[diam*jj] = st[diam*jj-diam] + st[diam*jj+diam] + st[diam*jj + 1] + st[diam*jj-diam+1] + st[diam*jj+diam+1]
            nei[diam*jj+diam-1] =st[diam*jj-2]+st[diam*jj+diam-2]+st[diam*jj+2*diam-2]+st[diam*jj-1]+st[diam*jj+2*diam-1]
        # the corners:
        if diam>1:
            nei[0] = st[1] + st[diam] + st[diam + 1]
            nei[diam-1] = st[diam-2] + st[2*diam-1] + st[2*diam-2]
            nei[diam*(diam-1)] = st[diam*(diam-1)+1] + st[diam*(diam-2)] + st[diam*(diam-2)+1]
            nei[diam*diam-1] = st[diam*diam-2] + st[diam*(diam-1)-1] + st[diam*(diam-1)-2]
        else:
            nei[0] = 0

        ##### Inter-chunk contribution to our chunk:
        above = (yChunk-1+self.chunksY) % self.chunksY # wrap-around.
        below = (yChunk+1)              % self.chunksY #wrap around.

        if xChunk>0:
            # The chunk to the left of us:
            chunk = state[yChunk + self.chunksY*(xChunk - 1)]
            for ii in range(1, diam-1):
                nei[ii] += chunk[diam*(diam-1)+ii] + chunk[diam*(diam-1)+ii - 1] + chunk[diam*(diam-1)+ii + 1]
            nei[0] += chunk[diam*(diam-1)] + chunk[diam*(diam-1) + 1]
            if diam>1:
                nei[diam-1] += chunk[diam*diam-2] + chunk[diam*diam-1]
    
            # The chunk northwest of us:
            nei[0] += state[above + self.chunksY*(xChunk - 1)][diam*diam - 1]

            # The chunk southwest of us:
            nei[diam-1] += state[below + self.chunksY*(xChunk - 1)][diam*(diam-1)]
    
        if xChunk<self.chunksX-1:
            # The chunk to the right of us:
            chunk = state[yChunk + self.chunksY*(xChunk + 1)]
            for ii in range(1, diam-1):
                nei[ii + diam*(diam-1)] += chunk[ii] + chunk[ii-1] + chunk[ii+1]
            nei[diam*(diam-1)] += chunk[0] + chunk[1]
            if diam>1:
                nei[diam*diam-1] += chunk[diam-2] + chunk[diam-1]
    
            # The chunk northeast of us:
            nei[diam*(diam-1)] += state[above + self.chunksY*(xChunk + 1)][diam-1]

            # The chunk southeast of us:
            nei[diam*diam - 1] += state[below + self.chunksY*(xChunk + 1)][0]

        # The chunk above us:
        chunk = state[above + self.chunksY*xChunk]
        for jj in range(1, diam-1):
            nei[diam*jj] += chunk[diam*jj + diam - 1] + chunk[diam*jj + 2*diam - 1] + chunk[diam*jj - 1]
        nei[0] += chunk[diam - 1] + chunk[2*diam - 1]
        if diam>1:
            nei[diam*(diam-1)] += chunk[diam*diam - 1] + chunk[diam*(diam -1) - 1]
        
        # The chunk below us:
        chunk = state[below + self.chunksY*xChunk]
        for jj in range(1, diam-1):
            nei[diam*jj + diam - 1] += chunk[diam*jj - diam] + chunk[diam*jj] + chunk[diam*jj + diam]
        nei[diam - 1] += chunk[0] + chunk[diam]
        if diam>1:
            nei[diam*diam - 1] += chunk[diam*(diam-1)] + chunk[diam*(diam-2)]
    
    cdef void stateUpdate(self, int ** state, int ** neighbors, int xChunk, int yChunk):
        # applies Conways 23/3 to a chunk.
        # Safe if they are the same array as this is a 1:1 map.
        cdef int diam = self.chunkDiam
        cdef size_t uu
        cdef int chunkID = self.chunksY*xChunk + yChunk
        cdef int * st = state[chunkID]
        cdef int * nei = neighbors[chunkID]
        for uu in range(diam*diam):
            if st[uu]>0: # survive on 2/3
                if nei[uu] == 2 or nei[uu] == 3: # nextst temporaly was holding the live-neighbor count.
                    st[uu] = 1
                else:
                    st[uu] = 0
            else: # birth on 3
                if nei[uu] == 3: # nextst temporaly was holding the live-neighbor count.
                    st[uu] = 1
                else:
                    st[uu] = 0

    cdef int neighborHunt(self, int * score, int xChunk, int yChunk, int target):
        # Returns 1 if at least one neighbor chunk has target, returns zero otherwize.
        cdef int hit = 0
        cdef int above = (yChunk-1+self.chunksY) % self.chunksY
        cdef int below = (yChunk+1)              % self.chunksY
        if xChunk>0:
            if score[below + self.chunksY*(xChunk-1)]==target:
                hit = 1
            if score[yChunk + self.chunksY*(xChunk-1)]==target:
                hit = 1
            if score[above + self.chunksY*(xChunk-1)]==target:
                hit = 1
        if xChunk<self.chunksX-1:
            if score[below + self.chunksY*(xChunk+1)]==target:
                hit = 1
            if score[yChunk + self.chunksY*(xChunk+1)]==target:
                hit = 1
            if score[above + self.chunksY*(xChunk+1)]==target:
                hit = 1
        if score[below + self.chunksY*xChunk]==target:
            hit = 1
        if score[above + self.chunksY*xChunk]==target:
            hit = 1
        return hit


    def step(self): # single step of conways life.
        cdef size_t i
        cdef size_t j
        cdef size_t u
        cdef size_t uu
        cdef int change
        cdef int * ref
        cdef int * st
        cdef int hasBuffer
        cdef int cellsPerChunk = self.chunkDiam*self.chunkDiam
        cdef int below
        cdef int above
        
        # main step:
        # active = 0 => don't do.
        # active = 1 => periodic chunk sournded by periodic chunks. Simulate but reset every globalPeriod.
        # active = 2 => Periodic bordering non-periodic. Since it was periodic from b4 to now, active=1 chunks are safe to reset.
                        # Run normlay.
        # active = 3 => Non-periodic, run normally.
        
        for i in range(self.chunksY): # Accumilate neighbors.
            for j in range(self.chunksX):
                if self.active[i + self.chunksY*j] > 0:
                    self.neighborcount(self.nextstate, self.state, j, i)
        for i in range(self.chunksY): # Apply conways rule.
            for j in range(self.chunksX):
                if self.active[i + self.chunksY*j] > 0:
                    self.stateUpdate(self.state, self.nextstate, j, i)

        # CONVENTION: when self.time divides evenly into self.periodic, the state is fully up to date.
        self.time = self.time + 1
        
        # Periodicity/activeness update, etc.
        if self.time % self.globalPeriod == 0:

            # Set periodic chunks to active=0, non-perioodic to active=3, and for active=1 chunks load the ref array.
            for u in range(self.chunksY*self.chunksX):
                if self.active[u] > 0:
                    st = self.state[u]
                    ref = self.referenceState[u]
                    # inner boundary chunks need to be reset:
                    if self.active[u] == 1:
                        for uu in range(cellsPerChunk):
                            st[uu] = ref[uu]
                        self.active[u] = 0
                    # We don't know if periodic. So check:
                    if self.active[u] >= 2:
                        change = 0
                        ref = self.referenceState[u]
                        st = self.state[u]
                        for uu in range(cellsPerChunk):
                            if ref[uu] != st[uu]:
                                change = 1
                
                        # Update ref if changed:
                        if change==1:
                            self.active[u] = 3
                            for uu in range(cellsPerChunk):
                                ref[uu] = st[uu]
                        if change==0:
                            self.active[u] = 0

            # Step 2: Set chunks within one of aperiodic chunks to active = 2.
            for i in range(self.chunksY): # Accumilate neighbors.
                for j in range(self.chunksX):
                    if self.active[i + self.chunksY*j]==0:
                        if self.neighborHunt(self.active, j, i, 3)> 0:
                            self.active[i + self.chunksY*j] = 2
            
            # Step 3: Set chunks within two of aperiodic chunks to active = 1.
            for i in range(self.chunksY): # Accumilate neighbors.
                for j in range(self.chunksX):
                    if self.active[i + self.chunksY*j]==0:
                        if self.neighborHunt(self.active, j, i, 2)> 0:
                            self.active[i + self.chunksY*j] = 1
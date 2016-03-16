# use "life" for the latest version, or "lifeStable as life" for a reliable version:
import life
import math
import time
# New Cython rules:
#  Using numpy for pattern arrays. It is faster and makes cleaner code.
    # Printing the numpy array is the same orienation as the pattern.
# WARNING: you must run this code twice every time the Cython code is updated.
    # (alternativly you could run "python3 setup.py build_ext --inplace" first instead).
    # If Cython fails to compile, it will run with the last sucessful compile.

import random
import time
import matplotlib.animation as animation
from subprocess import call
from operator import add, sub, mul# div
from imp import reload

# Very simple imaging, only sufficient for debugging:
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

# Makes random data for testing the algorythim on:
def randData(x,y):
    out = np.zeros((x,y), np.int)
    for i in range(x):
        for j in range(y):
            out[i,j]= round(random.random()*0.58)
    return out

#def normalize01(im):
    # The anim only auto-colorbars on the first frame, and we get stuck with that.
    # To fix this, we set the colorbar to [0,1], disable auto, and normalize the image to 01.
    #    lowest = np.amin(im)
    #    highest = np.amax(im)
    #  if lowest<highest:
    #     im = np.multiply(np.subtract(im, lowest), 1.0/(highest-lowest))
# return im

# Call this to import it:
call(["python3","setup.py","build_ext","--inplace"])
life = reload(life) # reload it because we built it, but will have to be called twice.
land = life.Life()

data0 = randData(1000,700)

for i in range(16): # North-west half-strip to test orienation.
    data0[0,i] = 1

land.setPatternAndChunk(data0,10)



# animation example:
# http://stackoverflow.com/questions/18743673/show-consecutive-images-arrays-with-imshow-as-repeating-animation-in-python


def getIm(step = 0):
    # anything outside [0 1] is clipped.
    showCells = 0.75 #[0,1]
    showGrid = 0.0 # [0,1].
    showActive = -0.5/3.0 #[0,1,2,3]
    shift = 0.75
    
    im = np.add(np.multiply(land.getPattern(), showCells), np.multiply(land.chunkerBoard(), showGrid))
    im = np.add(im, np.multiply(land.activeBoard(), showActive))
    im = np.add(im,shift)
    
    #im = normalize01(im)
    #print(im.tolist())
    
    return im

def profile():
    # A simple performance test.
    t0 = time.time()
    steps = 100
    for i in range(steps):
        land.step()
    t1 = time.time()
    print("time taken: "+str((t1-t0)/steps)+ " s. Grid size: "+(str(land.getPattern().shape)))


fig = plt.figure()
im = plt.imshow(getIm(),clim=(0.0, 1.0), interpolation='hanning',cmap=plt.get_cmap('Blues'))

#profile()


def animationStep(j):
    substeps = 1
    for i in range(substeps):
        land.step()
    im.set_array(getIm(j))
    return im

ani = animation.FuncAnimation(fig, animationStep, frames=range(1000000), interval=30) #blit=True
x = plt.show()

#print(map.makeMemoryError())

#plt.show(list2image(randData(10,10)))

#time.sleep(1.0)
import matplotlib.pyplot as plt
import numpy as np
import math
import itertools

#from matplotlib.figure import Figure

def clearFigure():
    return [{'clear': None}]

# Makes a simple y vs x plot.
def linePlot(ex, wy, exLabel, wyLabel, title):
    if ex is None:
        ex = np.arange(len(wy))
    if type(ex) is list:
        ex = np.asarray(ex)
    if type(wy) is list:
        wy = np.asarray(wy)
    cmds = []
    cmds.append({'linePlot': [ex, wy]})
    cmds.append({'xlabel': exLabel})
    cmds.append({'ylabel': wyLabel})
    cmds.append({'title': title})
    return cmds

def scatterPlot(ex, wy, exLabel, wyLabel, title):
    if ex is None:
        ex = numpy.arange(len(wy))
    if type(ex) is list:
        ex = np.asarray(ex)
    if type(wy) is list:
        wy = np.asarray(wy)
    cmds = []
    cmds.append({'scatterPlot': [ex, wy]})
    cmds.append({'xlabel': exLabel})
    cmds.append({'ylabel': wyLabel})
    cmds.append({'title': title}) 
    return cmds 

# Graph functions that can be called from any thread: they don't plot anything, but 
# they give us a list of commands that we then can (on the main thread) call tkinter on.
def multiImagePlot(imgs, titles):
    # TODO: put these into ecology?
    n = len(imgs)
    cmds = []
    cmds.append({'clear': None})
    cmds.append({'makeSubplot': n})
    for i in range(n):
        cmds.append({'subaxis': i})
        cmds.append({'image': imgs[i]})
        cmds.append({'title': titles[i]})
    return cmds

########### Now for the function that actually does the plotting ###########
# Only call from the main frame.
def actualize(mainFig, cmds):
    subF = None
    gridSpec = None
    gridSpecSize = None
    ax = None 
    for cmd in cmds:
        name = list(cmd.keys())[0]
        val = cmd[name]
        #print("Running plot cmd:",name)
        if name == 'clear':
            plt.clf()
        elif name == 'xlabel':
            plt.xlabel(val)
        elif name == 'ylabel':
            plt.ylabel(val)
        elif name == 'linePlot':
            if ax is None:
                ax = mainFig.add_subplot(1, 1, 1)
            ax.plot(val[0],val[1]) # two numpy arrays.
            #ax.show()
            #plt.show()
        elif name == 'scatterPlot':
            if ax is None:
                ax = plt.subplot(1, 1, 1)
            plt.plot(val[0],val[1], 'o') # no lines this time.
        elif name == 'makeSubplot':
            sizes = [[1,[1,1]], [2,[1,2]], [3,[1,3]], [4,[2,2]], [6,[2,3]], [9,[3,3]],
                     [12, [3,4]], [16, [4,4]], [20, [4,5]], [25, [5,5]], [36, [6,6]]]
            sz = [math.ceil(math.sqrt(val)), math.ceil(math.sqrt(val))]
            ls = list(itertools.dropwhile(lambda s: s[0]<val, sizes))
            if ls:
               sz = ls[0]
            gridSpecSize = [sz[1][0], sz[1][1]]
            gridSpec = plt.GridSpec(gridSpecSize[0],gridSpecSize[1])
        elif name == 'subaxis':
            #print("axpos:",val % gridSpecSize[0] , math.floor(val/gridSpecSize[0] + 1e-12))
            ax = mainFig.add_subplot(gridSpec[val % gridSpecSize[0] , math.floor(val/gridSpecSize[0] + 1e-12)])
        elif name == 'image':
            ax.imshow(np.transpose(val))
        elif name == 'title':
            ax.set_title(val)
        else:
            raise Exception('Unrecognized plot option:',name)
    mainFig.canvas.draw()
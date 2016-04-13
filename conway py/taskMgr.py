# Task manager.
import concurrent.futures
from subprocess import call

# pool.terminate()

def makePool():
    return concurrent.futures.ProcessPoolExecutor() #or use a ThreadPoolExecutor. Optional max_workers=4

state = {'pool': makePool(), 'status': 'free'}

def getPool(): # gets a pool that you can work with.
    return state['pool']

def busyWhenRunning(fn, *args, **kwargs): # makes the state busy as it runs the function, then returns the function.
    state['status'] = 'busy'
    out = fn(*args, **kwargs)
    state['status'] = 'free'
    return out

def future(fn, *args, **kwargs): # Gets a future object that you can call done() or result(timeout=None).
    return getPool().submit(fn, *args, **kwargs)

class anim: # non-blocking animations.
    # fn must accept one arg and return two args (i.e. a tuple):
        # What is passed back into the function the next time.
        # Whether we are done or not.
    # fnShow takes in the arg and does something with it.
    # fn runs on pool's threads. fnShow runs on the main thread.
    # tkinter ONLY works on the main thread, it can crash the program when called from other threads!
    # process pools make a copy of the object, so we need to extract it with futures.
    def __init__(self, fn, fnShow, arg):
        self.fn = fn
        self.fnShow = fnShow
        self.done = False
        self.arg = arg # What we put into fn at the beginning and what fn outputs each step.
        self.future = None    
    def everyFrame(self, show=None):
        # Shows the current state and schedules a future to run the function (if we aren't in the middle of it).
        # Show takes on three values:
            # 'off' : don't run the visualization function fnShow. The fastest.
            # 'update' : Run fnShow iff we got a change to the state or have just started.
            # 'always' : Run fnShow no matter what (the default).
        if show is None:
            show = 'always'
        if (self.future is not None) and self.future.done():
            self.arg, self.done = self.future.result()
        if (self.future is None) or self.future.done(): # an updateis needed.
            if show == 'update':
                self.fnShow(self.arg)
            if not self.done:
                self.future = future(self.fn, self.arg)
        if show == 'always':
            self.fnShow(self.arg)
    def show(self): # just calls fnShow, not needed if you are using everyFrame.
        self.fnShow(self.arg)
	
    

def abort(): # TODO: only terminate when we have a running task.
    state['pool'].terminate()
    state['pool'] = makePool()

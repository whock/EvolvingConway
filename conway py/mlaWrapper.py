# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 17:20:14 2016

@author: Will
Wrapper for mu/lambda/alpha  GA (based on hillClimbWrapped.py)
"""

from hillClimbWrapped import *
import random
import numpy as np


w = 50 # pattern size.
h = 150
chunk = 10 # MUST divide evenly with h or it may make a coorder that is debries-free.
# parameters for our environment:
worldW = 500 # entire width.
density = 0.1 # density of space junk.
# Core algorithm parameters:
time = 10000# how long we run before timing out.
initPatternDensity = 0.15 # initial random density.
replicates = 3# how many to average for the fitness function.
mutateRate = 0.05 # pointwise mutation.
reuseFitness = False # Never recalculate a fitness on a pattern if true.
N = 1

      
class mock():
    def __init__(self):
        self.pattern = []
        self.fitness = []

    def run(self):
        self.pattern = np.asarray([[random.random() for i in range(10)] for j in range(10)])
        self.fitness = random.randint(0,100)
 
gens = 100
pop =100
mu = 25
alpha = 0.5*(pop/mu)

class mla():
    def __init__(self,gens,pop,mu,alpha):
        self.elites = []
        self.i=1
        self.data = {}
        self.clones = []
        self.gens = gens # num generations
        self.pop = pop # pop size lambda (name reserved in python)
        self.mu = mu
        self.alpha = alpha # number of "children" that are copies of parent i.e. not mutated


    def get_fitness(self):
        fitness = []
        for i,k in enumerate(self.data):
            fitness.append((k,self.data[k][0].fitness))
            self.data[k][1].append(self.data[k][0].fitness)
        return fitness
            
    def kill(self):
        names = [i[0] for i in self.elites]
        for i,k in enumerate(self.data):
            if k not in names:
                del self.data[k]
          
    
    def init_data(self):
        for p in range(self.pop):
            self.data['Pattern_{}'.format(self.i+1)] = (mock(),[])
            self.i+=1 
        for i,k in enumerate(self.data):
            self.data[k][0].run()
          
    def sim(self):
        self.init_data()
        for t in range(self.gens):
            fitness = self.get_fitness()
            sortfit = sorted(fitness,key=lambda x:x[1],reverse=True)
            self.elites = sortfit[:self.mu+1]
            self.kill()
            for i,k in enumerate(self.data):
                for r in range(self.alpha):
                    self.data['Pattern_{}'.format(self.i+1)] = copy(self.data[k])
                    self.i+=1
                for m in range((self.pop/self.mu)-self.alpha):
                    self.data[k][0].mutate()
    
    
#climber = hillClimb(w,h,chunk,worldW,density,time,initPatternDensity,replicates,mutateRate,reuseFitness,N)
#climber.run()
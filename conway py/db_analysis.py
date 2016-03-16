# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 12:48:52 2016

@author: Will
"""
''' Database functionality.
Database structure. Each calendar day is a pickle file with DDMMYY.p as name
Within this: structure is nested dict.
Day > Individual sim (indexed by timestamp HHMMSS) > Patterns > Pattern
                                                              > Its fitness
                                                    > Parameters
'''
import pickle
import matplotlib.pyplot as plt
from sys import argv


def unscrew(day):
    with open(day+'.p','rb') as f:
        data = pickle.load(f)
    return data
    
def plot_pattern(data,day,ts,pattern):
    plt.imshow(data[day][ts]['Patterns'][pattern][0],interpolation='None',cmap='Greys')
    plt.title('Pattern {} from {} {}'.format(pattern,day,ts))
    
def plot_fitness(data,day,ts):
    fitness = []
    for i in data[day][ts]['Patterns']:
        fitness.append(i[1])
    plt.plot(fitness,'^')
    plt.title('Fitness plot from {} {}'.format(day,ts))
    
    plt.xlabel('Time',fontsize=18)
    plt.ylabel('Fitness',fontsize=18)

def get_max_pattern(data,day,ts,plot=True):
    '''Get pattern with max fitness, optional plot'''
    fitness = []
    for i in data[day][ts]['Patterns']:
        fitness.append(i[1])
    idx = fitness.index(max(fitness))
    pattern = data[day][ts]['Patterns'][idx][0]
    fit = data[day][ts]['Patterns'][idx][1]
    if plot:
        plt.imshow(pattern,interpolation='None',cmap='Greys')
        plt.title('Pattern {} from {} {} had max fit of {}'.format(idx,day,ts,fit))
    
    
    
    
    
    
    
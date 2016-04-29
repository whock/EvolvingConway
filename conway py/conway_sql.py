# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 11:48:11 2016

@author: whockei1
"""

import sqlite3 as lite
import random,datetime,os,functools,itertools,operator
import matplotlib.pyplot as plt
import numpy as np

def open_table():
    con = lite.connect('conwaysql.db')
    cur = con.cursor()
    return con,cur


def create_db():
    con=None
    con = lite.connect('conwaysql.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE Metadata(Id INT,Meta TEXT)")
    cur.execute("CREATE TABLE Patterns(Id INT,Pattern TEXT)")
    cur.execute("CREATE TABLE Data(Id INT,PatFitness TEXT,PopFitness TEXT, Other TEXT)")


def table_info(tname):
    '''get table metadata'''
    pass
    

def get_unique_ID():
    return datetime.datetime.now().strftime("%y%m%d_%H%M")
 

def package(table,data):  #MAIN FUNCTION to insert data
    '''single field'''
    stringed = stringify(data)
    insert(table,stringed)
    
    
def readout(table,uID): #MAIN FUNCTION to retrieve data
    data = query(table,uID)
    data = [destring(i,)]
    

def compress(data):
    '''remove all whitespace from a string'''
    return data.replace(" ","")
   
def insert(table,data):
    uID = get_unique_ID()
    data.insert(0,uID)
    cur.execute("INSERT INTO {} VALUES({})".format(table,data))
    con.commit()
    
def stringify(data):
    '''data is single field, eg metadata,pattern,fitness vec, etc. Assumed
    that elements of list / array are numeric'''
    stringed = []
    data = np.asarray(data) # easier to work with
    if len(data.shape) > 1: # check 2d or 1d
        _ = [[stringed.append(str(data[i,j])) for i in range(len(data))] for j in range(len(data[0]))]
    else:
        _ = [stringed.append(str(data[i])) for i in range(len(data))]
    stringed = compress(stringed)    
    return stringed

def reshape(data,rows,cols):
    '''take text data and reshape into matrix of floats, shape (rows,cols)'''
    data = [float(i) for i in data]
    return np.array(data).reshape(rows,cols)
    
def destring(data,ID,tname):
    if tname == 'Metadata':
        destringed = []
        meta = parse_meta([],ID)
        for k,v in meta.iteritems():
            destringed.append((k,v))
            
    elif tname == 'Patterns':
        parsed = parse_meta(['w','h'],ID)
        w = parsed['w']
        h = parsed['h']
        destringed = reshape(data,h,w)
        
    elif tname =='Data':
        data  = query('Data',ID)
        fit = data[1]
        popfit = data[2]
        other = data[3]
        destringed = [map(operator.methodcaller("split",","),i) for i in [fit,other]]
        if popfit != 'None':
            fitinfo = findsubstrings(other,['duration','popsize'])
            destringed.append(reshape(popfit,fitinfo['popsize'],fitinfo['duration']))
        destringed[0] = [float(i) for i in destringed[0]]
    return destringed


def query(tname,uID):
    cur.execute("SELECT * FROM {}".format(tname))
    rows = cur.fetchall()
    found = list(filter(lambda x: x[0]==uID,rows))
    if found == []:
        return 'Entry {} in {} does not yet exist'.format(uID,tname)
    else:
        return found
    
def findsubstrings(data,targets):
    m = data.split(',')
    h ={}
    if targets ==[]:
        for i in m:
            h[i[0].split(':')[0]] = float(i[0].split(':')[1])
    hits = [list(filter(lambda x: i in x,m)) for i in targets]
    if True in [len(i)>1 for i in hits]:
        return 'Ambiguous data naming - multiple hits for {}'.format(targets[[len(i)>1 for i in hits].index(True)])

    for i in hits:
        h[i[0].split(':')[0]] = float(i[0].split(':')[1])
    return h
 
def parse_meta(targets,uID):
    meta = query('Metadata',uID)
    hitdict = findsubstrings(meta[1],targets)
    return hitdict
       
def fin():
    con.close()

    
    
    
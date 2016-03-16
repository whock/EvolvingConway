# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 11:56:46 2016

@author: whockei1
"""

import tables
import platform
import numpy as np
import time

def get_path():
    if 'Win' in platform.platform() or 'win' in platform.platform():
        path = '.\conwaydb.h5'
    else:
        path = './conwaydb.h5'
    return path

def makedb(path):
    cdb = tables.open_file(path,'w') # THIS OVERWRITES EXISTING FILE
    return cdb
    
def open_db(path):
    cdb = tables.open_file(path,'a')
    return cdb

def naive_compress(pattern):
    matcomp = []
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            if pattern[i,j] == 1:
                matcomp.append([i,j])
    return matcomp
  
def create_table(date,conwaydb):
    '''Create a table corresponding to a lineage / tree of life in conway. Patterns are
    stored row-wise with column IDs showing when one pattern ends and another begins. Date in
    YYMMDD form for table ID, YYMMDD-HHMM for each pattern therein'''
    class Contable(tables.IsDescription):
        #pID = tables.StringCol(17)
        date = tables.StringCol(15)
        data = tables.Int64Col(shape=(1,2))
        #fitscore = tables.Int64Col()
        #fittype = tables.StringCol(75)
        #debristype = tables.StringCol(75)
    group = conwaydb.create_group('/','simulation')
    ctable = conwaydb.create_table(group,date,Contable,'Data for patterns with ECA on {}'.format(date))  
    
def add_data(ctb,i,pattern):
    '''meta refers to info in pID beyond date. Format as such GXX-MMRRUU
    '''
    dt = ctb.row
    data = naive_compress(pattern)
    for i in range(len(data)):
        #dt['pID'] = '{}-{}'.format(date,meta)
        dt['date'] = time.strftime("%Y%m%d-%H%M")+'-{}'.format(i)
        dt['data'] = (data[i][0],data[i][1])
        #dt['fitscore'] = fitscore
        #dt['fittype'] = fittype
        #dt['debristype'] = debristype
        dt.append()
    ctb.flush()
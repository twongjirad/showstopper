import os,sys
import numpy as np
import pandas as pd

__hootdb = None

def buildhootdb():
    global __hootdb
    hootdict = {'crate':[],'slot':[],'femch':[],
                'FT':[],'connect':[],'plane':[],'mbid':[],
                'asicid':[],'wireid':[]}
                
    for cratenum in xrange(1,10):
        f = open('hoot/crate%d.txt'%(cratenum),'r')
        lines = f.readlines()
        for l in lines[1:]:
            data = l.split()
            hootdict['crate'].append( int(data[0].strip()) )
            hootdict['slot'].append( int(data[1].strip()) )
            hootdict['femch'].append( int(data[2].strip()) )
            hootdict['FT'].append( int(data[3].strip()) )
            hootdict['connect'].append( data[4].strip() )
            hootdict['plane'].append( data[6].strip() )
            hootdict['mbid'].append( int(data[7].strip()) )
            hootdict['asicid'].append( int(data[8].strip()) )
            hootdict['wireid'].append( int(data[0].strip() ) )
    __hootdb = pd.DataFrame( hootdict )
    
def gethootdb():
    global __hootdb
    if __hootdb is None:
        buildhootdb()
    return __hootdb


if __name__=="__main__":
    db = gethootdb()
    print db

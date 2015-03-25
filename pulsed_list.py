import os,sys
import numpy as np
import pandas as pd

def get_pulsed_channel_list( version=2 ):
    if version==1:
        # broken
        filename = 'runmeta/run0%d_pulsed_ch.txt'%(run)
        mydata = np.genfromtxt( filename, dtype=np.int )
        return pd.DataFrame( mydata, columns=['crate','slot','femch'] )
    else:
        data = {"run":[],
                "subrun1":[],
                "subrun2":[],
                "pulsed_crate":[],
                "pulsed_slot":[],
                "pulsed_femch":[],
                "ref_crate":[],
                "ref_slot":[],
                "ref_femch":[] }
        f = open('runmeta/pulsed_list.txt','r')
        lines = f.readlines()
        nlines = 0
        for l in lines[1:]:
            if l.strip()=='':
                continue
            runcode = l.strip().split()[0]
            pulsedcode = l.split()[1]

            data['run'].append( int(runcode.split(",")[0]) )
            data['subrun1'].append( int(runcode.split(",")[1]) )
            data['subrun2'].append( int(runcode.split(",")[2]) )
            data['pulsed_crate'].append( int(pulsedcode.split(":")[0]) )
            data['pulsed_slot'].append( int(pulsedcode.split(":")[1]) )
            data['pulsed_femch'].append( int(pulsedcode.split(":")[2]) )
            try:
                refcode = l.split()[2]
                data['ref_crate'].append( int(refcode.split(":")[0]) )
                data['ref_slot'].append( int(refcode.split(":")[1]) )
                data['ref_femch'].append( int(refcode.split(":")[2]) )
            except:
                data['ref_crate'].append( int(pulsedcode.split(":")[0]) )
                data['ref_slot'].append( int(pulsedcode.split(":")[1]) )
                data['ref_femch'].append( int(pulsedcode.split(":")[2]) )
            nlines += 1
        
        # table check
        for name,value in data.items():
            if len(value)!=nlines:
                raise RunTimeError('%s has wrong number of entries %d not %d'%(name,len(value),nlines))
            
        return pd.DataFrame( data )

if __name__ == "__main__":
    plist = get_pulsed_channel_list()
    print plist

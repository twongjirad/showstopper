import os,sys
import numpy as np
import ROOT
from root_numpy import root2array, root2rec, tree2rec
import pandas as pd
from badchtable import get_badchtable
from pulsed_list import get_pulsed_channel_list

def get_index( crate, slot, femch ):
    index = crate*64*15 + (slot-4)*64 + femch
    return index

def get_pulsed_index_array( pulsed_list ):
    pulsed_indices = []
    for (crate,slot,femch) in pulsed_list:
        index = get_index( crate,slot,femch )
        pulsed_indices.append( index )
    return pulsed_indices

def make_adc_matrix():

    maxadc_matrix  = np.zeros( (9600,9600) )
    nfilled_matrix = np.zeros( (9600,9600) )

    for run in xrange(28,46):
        npzfile = 'output/run%03d.npz'%(run)
        if not os.path.exists(npzfile):
            print "skip ",npzfile
            continue
        datanpz = np.load( npzfile )
        data = datanpz['outdf']
        print "extracting ",npzfile

        pulsed_np = get_pulsed_channel_list( run )
        pulsed_list = pulsed_np.values.tolist()
        pulsed_indices = get_pulsed_index_array( pulsed_list )
    
        for i in xrange(0,data.shape[0]):
            crate  = data[i,0]
            slot   = data[i,1]
            femch  = data[i,2]
            maxadc = data[i,3]
            pulsed = data[i,4]

            if pulsed==0:
                # not pulsed
                # we fill over the pulsed channels
                unpulsed_index =  get_index( crate, slot, femch )
                for pulsed_index in pulsed_indices:
                    maxadc_matrix[pulsed_index,unpulsed_index]  += maxadc
                    nfilled_matrix[pulsed_index,unpulsed_index] += 1.0
            if i%500==0:
                print "entry",i
    nfilled_matrix[ nfilled_matrix==0 ] = 1.0
    maxadc_matrix /= nfilled_matrix
    return maxadc_matrix

if __name__ == "__main__":
    
    result = make_adc_matrix()
    print result
    np.save('maxadc',result)

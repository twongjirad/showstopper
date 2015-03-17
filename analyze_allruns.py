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
    nfilled_matrix = np.zeros( (9600,9600), dtype=np.int )

    # we now fill
    for run in xrange(28,45):
        if run==31:
            continue

        npzfile = 'output/run%03d.npz'%(run)
        if not os.path.exists(npzfile):
            print "skip ",npzfile
            continue

        print "extracting ",npzfile
        datanpz = np.load( npzfile )
        data = datanpz['outdf']
        df = pd.DataFrame( data )
        
        # index channels
        df['hist_index'] = np.vectorize( get_index )( df['crate'], df['slot'], df['femch'] )

        # get pulsed list
        pulsed = df[ df['pulsed']==1 ]
        pulsed.drop( 'index', axis=1, inplace=True )

        #unpulsed = df[ df['pulsed']==0 ]
        #unpulsed.drop( 'index', axis=1, inplace=True )

        for r in data:
            # we fill over the pulsed channels
            unpulsed_index =  get_index( r['crate'], r['slot'], r['femch'] )
            for pulsed_index in pulsed['hist_index']:
                if nfilled_matrix[pulsed_index,unpulsed_index]==0:
                    maxadc_matrix[pulsed_index,unpulsed_index]  += r['mean_amp']
                    nfilled_matrix[pulsed_index,unpulsed_index] += 1
    nfilled_matrix[ nfilled_matrix==0 ] = 1.0
    maxadc_matrix /= nfilled_matrix
    return maxadc_matrix

if __name__ == "__main__":
    
    result = make_adc_matrix()
    print result
    np.savez('maxadc',mat=result)

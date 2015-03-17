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

def make_adc_matrix(run):

    ampcov  = np.zeros( (9600,9600) )

    npzfile = 'output/run%03d.npz'%(run)
    if not os.path.exists(npzfile):
        print "skip ",npzfile
        return

    print "extracting ",npzfile
    datanpz = np.load( npzfile )
    data = datanpz['outdf']
    df = pd.DataFrame( data )
        
    # index channels
    df['hist_index'] = np.vectorize( get_index )( df['crate'], df['slot'], df['femch'] )
    df.drop( 'index', axis=1, inplace=True )
    print df.columns
    outarr = df.to_records()

    #x1 = df.sort('hist_index')['mean_amp'].values
    x1 = df.sort('hist_index')['max_amp'].values
    y1 = np.zeros(9600)
    y1[ df.sort('hist_index')['hist_index'].values ] = x1[:]

    #x1[:] /= df['mean_ped_mean'].values
    xx = np.outer( y1, y1 )
    xx = np.sqrt(xx)
    pulsed = df[ df['pulsed']==1 ]['hist_index'].values
    badch = df[ df['badch']==1 ]['hist_index'].values
    print "NPULSED:",len(pulsed)
    print pulsed
    return xx, pulsed,badch


if __name__ == "__main__":
    
    run = 83
    result,pulsed,badch = make_adc_matrix(run)
    np.savez('covamp_run%03d'%(run),mat=result,pulsedlist=pulsed,badchlist=badch)

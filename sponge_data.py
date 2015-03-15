import os,sys
import numpy as np
import ROOT
from root_numpy import root2array, root2rec, tree2rec, array2root
import pandas as pd
from badchtable import get_badchtable
from pulsed_list import get_pulsed_channel_list

def import_data( ptree_filename ):
    """Imports pulse tree and outputs list of numpy arrays"""
    arr = root2array( ptree_filename, 'ptree' )
    return arr

def get_channel_groups( df ):
    chs = df.groupby( ('crate','slot','femch') )
    return chs

def get_run_data( run ):
    filename = 'data/pulser_run0%d.root'%(run) 
    if not os.path.exists(filename):
        return None
    arr = import_data( filename )
    return arr
    

def sponge_run( run ):

    out_npz = 'output/run%03d.npz'%(run)
    if os.path.exists(out_npz):
        print "NPZ for Run ",run," already made"
        return

    print "PROCESSING: ",out_npz

    # crate  slot  femch     ped_mean   ped_rms         amp      charge
    a = get_run_data(run)
    if a==None:
        print "No data for run: ",a
        return
    df = pd.DataFrame(a)

    # get bad channel table
    badch = get_badchtable()
    badch_list = badch[['Crate','Slot','FEM Channel']].values.tolist()

    # tag bad channels
    df['badch'] = np.vectorize( lambda x,y,z: 1 if [x,y,z] in badch_list else 0 )( df['crate'], df['slot'], df['femch'] )

    chs = get_channel_groups( df )    

    print "Number of groups: ",len(chs)

    # get max of each column for each group
    maxch = chs.aggregate(np.max)

    # if adc is above a threshold, then mark it as a pulsed channel
    maxch['pulsed'] = maxch['amp'].apply( lambda x: 1 if x>1000.0 else 0 )

    print "NPULSED: ",len( maxch[ maxch['pulsed']==1 ] )
    print "NPULSED and BADCH: ",len( maxch.query( '(pulsed==1) & (badch==1)' ) )

    outdf = pd.DataFrame( maxch ).reset_index()

    print "Writing ",out_npz
    np.savez( out_npz, outdf=outdf.to_records() )

    array2root( outdf.to_records(), 'output/run%03d.root'%(run),'maxamp' )

    
if __name__=="__main__":
    for x in xrange(28,60):
        sponge_run( x )

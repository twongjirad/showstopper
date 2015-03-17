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
        print "Did not Find: ",filename
        return None
    arr = import_data( filename )
    df = pd.DataFrame(arr)
    return df
    

def sponge_run( run, use_pulsed_list=False, remake=False ):

    out_npz = 'output/run%03d.npz'%(run)
    if os.path.exists(out_npz) and not remake:
        print "NPZ for Run ",run," already made"
        return

    print "PROCESSING: ",out_npz

    # crate  slot  femch     ped_mean   ped_rms         amp      charge
    df = get_run_data(run)
    if df is None:
        print "No data for run: ",a
        return

    # get bad channel table
    badch = get_badchtable()
    badch_list = badch[['Crate','Slot','FEM Channel']].values.tolist()

    # pulsed channel list
    if use_pulsed_list:
        pulsed_df = get_pulsed_channel_list(run)
        print pulsed_df
        pulsed_list = pulsed_df[['crate','slot','femch']].values.tolist()
        print "LOADED PULSED CHANNELS RECORDED: ",len(pulsed_list)

    chs = get_channel_groups( df[ df['amp']>10 ] )    

    print "Number of groups: ",len(chs)

    # get max, mean of each column for each group
    maxch  = chs.aggregate(np.max)
    meanch = chs.aggregate(np.mean)

    max_cols = []
    for col in maxch.columns:
        max_cols.append( "max_%s"%(col) )
    maxch.columns = max_cols
    mean_cols = []
    for col in meanch.columns:
        mean_cols.append( "mean_%s"%(col) )
    meanch.columns = mean_cols
    dfmax  = pd.DataFrame( maxch )
    dfmean = pd.DataFrame( meanch )
    outdf = dfmax.join( dfmean ).reset_index()

    # if adc is above a threshold, then mark it as a pulsed channel
    if use_pulsed_list:
        outdf['pulsed'] = np.vectorize( lambda x,y,z: 1 if [x,y,z] in pulsed_list else 0 )( outdf['crate'], outdf['slot'], outdf['femch'] )
    else:
        outdf['pulsed'] = outdf['max_amp'].apply( lambda x: 1 if x>700.0 else 0 )

    # tag bad channels
    outdf['badch'] = np.vectorize( lambda x,y,z: 1 if [x,y,z] in badch_list else 0 )( outdf['crate'], outdf['slot'], outdf['femch'] )

    print "NPULSED: ",len( outdf[ outdf['pulsed']==1 ] )
    print "NPULSED and BADCH: ",len( outdf.query( '(pulsed==1) & (badch==1)' ) )
    
    print "Writing ",out_npz
    np.savez( out_npz, outdf=outdf.to_records() )

    array2root( outdf.to_records(), 'output/run%03d.root'%(run),'maxamp' )

if __name__=="__main__":
    for x in xrange(83,85):
        sponge_run( x, use_pulsed_list=False, remake=True )

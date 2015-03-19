import os
import numpy as np
import pandas as pd
from root_numpy import root2array, root2rec, tree2rec, array2root
from channelmap import getChannelMap

rmax = 5100.0
gmax = 3000.0
bmax = 1100.0
tstart = 0
tend = 100

def get_run_datafiles( run ):
    datadir = os.listdir('data')
    datafiles = {}
    subrunlist = []
    for d in datadir:
        if "run%03d"%(run) in d:
            try:
                subrun1 = int(d.split("_")[2][len('subrun'):])
                subrun2 = int(d.split("_")[3].split('.')[0])
                subrunlist.append( (subrun1,subrun2))
                datafiles[(subrun1,subrun2)] = 'data/%s'%(d)
                print subrun1,subrun2,d
            except:
                continue
    return subrunlist,datafiles

def get_dataframes(datafile):
    wf_arr= root2array( datafile, 'wftree' )
    wfdf = pd.DataFrame( wf_arr )
    pl_arr = root2array( datafile, 'ptree' )
    pldf = pd.DataFrame( pl_arr )
    return wfdf, pldf

#def fft_rgba( wfarr ):
def fft_rgba( wfrow, mean ):
    #print wfrow
    #wfarr = np.array( wfrow )
    wfarr = wfrow
    wfarr[:] -= mean
    xff = np.fft.fft( wfarr[tstart:tend] )
    xffc = np.conjugate( xff )
    xx = np.sqrt(np.real(xff*xffc))
    
    rval = np.max( xx[4:7] )
    gval = np.max( xx[14:17] )
    bval = np.max( xx[24:27] )
    amp = np.max(  wfarr[:] )
    return rval,gval,bval,1.0,amp

def add_fft_rgba( wfdf ):
    rgba = np.vectorize( fft_rgba )( wfdf['wf'], wfdf['ped_mean'] )
    wfdf['rval'] = rgba[0][:]
    wfdf['gval'] = rgba[1][:]
    wfdf['bval'] = rgba[2][:]
    wfdf['aval'] = rgba[3][:]
    wfdf['rratio'] = rgba[0][:]/rmax
    wfdf['gratio'] = rgba[1][:]/gmax
    wfdf['bratio'] = rgba[2][:]/bmax
    wfdf['max_amp'] = rgba[4][:]

def map_plane( crate, slot, femch ):
    chmap = getChannelMap()
    try:
        plane = chmap.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(crate,slot,femch) )['plane'].values[0]
        return plane
    except:
        print "did not find: ",crate,slot,femch
        return None

def map_channel( crate, slot, femch ):
    chmap = getChannelMap()
    try:
        wireid = chmap.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(crate,slot,femch) )['wireid'].values[0]
        return wireid
    except:
        print "did not find: ",crate,slot,femch
        return None

def fft_spunge(run,remake=False):
    global tstart
    global tend
    subrunlist, datafilenames = get_run_datafiles( run )
    chmap = getChannelMap()
    for subrun in subrunlist:
        if run==95 and subrun==(27,36):
            tstart = 1400
            tend = 1500
        elif run==95 and subrun==(217,226):
            tstart = 1800
            tend = 1900
        else:
            tstart = 0
            tend = 100
        print "RUN ",run," ",subrun,": ",tstart,tend
        outfile = "output/run%03d_subrun%03d_%03d" % (run,subrun[0],subrun[1])
        #if os.path.exists(outfile+".npz") and (remake==False or subrun!=(217,226)):
        if os.path.exists(outfile+".npz") and (remake==False):
            print outfile," already exists. skipping"
            continue
        print datafilenames[subrun]
        wfdf, pldf = get_dataframes( datafilenames[subrun] )
        #tempdf = wfdf[:20].copy()
        #add_fft_rgba( tempdf )
        #print tempdf
        add_fft_rgba( wfdf )
        #print wfdf.first
        #print "Add plane column"
        #wfdf['plane'] = np.vectorize( map_channel )( wfdf['crate'], wfdf['slot'], wfdf['femch'] )
        #print "Add wire id"
        #wfdf['wireid'] = np.vectorize( map_channel )( wfdf['crate'], wfdf['slot'], wfdf['femch'] )
        #pickup = wfdf.query( '(rval>0.05) | (bval>0.05) | (gval>0.05)' )
        #print pickup
        print "saving :",outfile
        np.savez( outfile, wffftrgba=wfdf.to_records() )


if __name__ == "__main__":
    
    fft_spunge(83,remake=True)

import os,sys
import StringIO
import numpy as np
import pandas as pd
from root_numpy import root2array, root2rec, tree2rec, array2root
from hoot import gethootdb
from pulsed_list import get_pulsed_channel_list

tstart = 0
tend = 100

def load_data( run, subrun1, subrun2 ):
    datafilename = 'data2/pulser_run%03d_subrun%03d_%03d.root'%(run,subrun1,subrun2)
    print "Loading file: ",datafilename
    wf_arr = root2array( datafilename, 'wftree' )
    wfdf = pd.DataFrame( wf_arr )
    pl_arr = root2array( datafilename, 'ptree' )
    pldf = pd.DataFrame( pl_arr )
    return wfdf, pldf

def runningMeanFast(x, N):
    return np.convolve(x, np.ones((N,))/N)[(N-1):]

def get_power_spectrum( arr ):
    xff = np.fft.fft( arr[tstart:tend] )
    xffc = np.conjugate( xff )
    xx = np.sqrt(np.real(xff*xffc))
    return xx

def generate_products( wf ):
    """ for each waveform generate the products we are interested in."""
    arr = np.array( wf )
    tlen = tend-tstart
    # remove mean
    arr[:] -= np.mean( arr[tend:tend+tlen] )
    smoothed = runningMeanFast( arr, 5 )
    fft = get_power_spectrum( arr )
    #smo_fft = runningMeanFast( fft, 5 )

    # products
    maxamp = np.max( np.abs(arr[tstart:tend]) )
    rms = np.std( wf[tend:tend+tlen] )
    smo_maxamp  = np.max( np.abs( smoothed[tstart:tend] ) )
    smo_rms = np.std( smoothed[tend:tend+tlen] )
    rval = np.max( fft[4:7] )
    gval = np.max( fft[14:17] )
    bval = np.max( fft[24:27] )
    amp_ratio = smo_maxamp/smo_rms
    return maxamp,rms,smo_maxamp,smo_rms,rval,gval,bval,amp_ratio

def process_channel( wfdf_input, pulsed_ch, pulsed_slot, pulsed_femch ):
    """ Process the data. 

    We generate the following for each channel:
    - a smoothed waveform.
    - a power spectrum.
    - Power spectrum RGB values.
    """
    
    # get pulsed info
    # wfdf = wfdf_input.ix[1000:1010] # for testing on small sample
    wfdf = wfdf_input # process whole tree
    indexed = wfdf_input.set_index(['crate','slot','femch'])
    pulsed_ch = indexed.loc[pulsed_ch, pulsed_slot, pulsed_femch]
    maxadc = np.max( pulsed_ch['wf'] )
    products = np.vectorize( generate_products )( wfdf['wf'] )
    
    # appen products to the table
    wfdf['wfamp'] = products[0][:]
    wfdf['wfrms'] = products[1][:]
    wfdf['smo_maxamp'] = products[2][:]
    wfdf['smo_rms'] = products[3][:]
    wfdf['rval'] = products[4][:]
    wfdf['bval'] = products[5][:]
    wfdf['gval'] = products[6][:]
    wfdf['amp_ratio'] = products[7][:]
    return wfdf

def hooty_and_the_volefish( wfdf ):
    hootdb = gethootdb()
    return wfdf.join( hootdb.set_index(['crate','slot','femch']), on=['crate','slot','femch'] )

def process_run( run, subrun1, subrun2 ):
    wfdf, pldf = load_data( run, subrun1, subrun2 )
    outdf = process_channel( wfdf, 2, 6, 0 )
    outdf = hooty_and_the_volefish( outdf )
    return outdf

def get_statistics( df, amprms_ratio_cut, max_amp_cut, pulsed_channel, ref_channel=None,  outfile=None ):
    indexed = df.set_index(['crate','slot','femch'])
    if ref_channel is None:
        ref_channel = pulsed_channel
    ref_ch = indexed.loc[ref_channel[0],ref_channel[1],ref_channel[2]]
    maxadc = ref_ch['wfamp']
    rmax = ref_ch['rval']
    gmax = ref_ch['gval']
    bmax = ref_ch['bval']

    pulsed_crate = pulsed_channel[0]
    pulsed_slot  = pulsed_channel[1]
    pulsed_femch = pulsed_channel[2]
    pulsed_ch = indexed.loc[pulsed_crate,pulsed_slot,pulsed_femch]

    query = '(amp_ratio>%.4f & wfamp/%.4f>%.04f & not (crate==%d & slot==%d & femch==%d) )'%(amprms_ratio_cut,maxadc,max_amp_cut, pulsed_crate, pulsed_slot, pulsed_femch)
    print "SELECTION: ",query
    pickupdf = df.query( query )
    npickup = len(pickupdf)
    print "REFERENCE MAX ADC: ",maxadc
    print "PULSED MAX ADC: ",pulsed_ch['max_amp']
    
    # different categories
    categories = [ 'sameasic', 'samemb_connector', 'samemb','sameFT','diffFT' ]
    cat_query = { 'sameasic':'asicid==%d'%(pulsed_ch['asicid']),
                  'samemb_connector':'mbid==%d & connect=="%s"'%(pulsed_ch['mbid'],pulsed_ch['connect']),
                  'connector':'connect=="%s" & FT==%d'%(pulsed_ch['connect'],pulsed_ch['FT']),
                  'samemb':'mbid==%d'%(pulsed_ch['mbid']),
                  'sameFT':'FT==%d'%(pulsed_ch['FT']),
                  'diffFT':'FT!=%d'%(pulsed_ch['FT']) }
    cat_description = {'sameasic':'Same ASIC',
                       'samemb_connector':'Same MB and Connector',
                       'connector':'Same Connector and FT',
                       'samemb':'Same MB',
                       'sameFT':'Same FT',
                       'diffFT':'Different FT'}

    stats = StringIO.StringIO()
    print >> stats,  "PICKUP QUERY: ",query
    print >> stats,  "Number of pickup pulses: ",npickup
    if npickup>0:
        print >> stats,  "------------------------------------------------"
        print >> stats,  "Category    |  N in category  | pickup in category  |  pct of category  |  pct. of all pulses"
        notpulsed = " not (crate==%d & slot==%d & femch==%d)"%(pulsed_crate, pulsed_slot, pulsed_femch)
        for cat in categories:
            ncat = len(df.query( cat_query[cat]+" & "+notpulsed ))
            ncat_pickup = len(df.query( cat_query[cat]+" & "+query ))
            print >> stats,  cat_description[cat]," | ", ncat," | ",ncat_pickup," | ",float(ncat_pickup)/float(ncat)*100," | ",float(ncat_pickup)/float(npickup)*100
        print stats.getvalue()
        print >> stats,''
        print >> stats,"PICKUP CHANNELS"
        print >> stats, pickupdf.reset_index()[['crate','slot','femch','FT','connect','mbid','asicid','max_amp','amp_ratio']].to_string()
    if outfile is not None:
        f = open(outfile,'w')
        f.write( stats.getvalue()+"\n")
    
if __name__ == "__main__":
    remake = False
    pulseddf = get_pulsed_channel_list()
    data_files = os.listdir("data2")
    for data in data_files:
        if ".root" not in data:
            continue
        print data
        parts = data[:-len(".root")].split("_")
        run = int(parts[1][len("run"):])
        subrun1 = int(parts[2][len("subrun"):])
        subrun2 = int(parts[3])
        npfilename = 'output_crosstalk/numpy/run%03d_subrun%03d_%03d'%(run,subrun1,subrun2)
        pulsed = pulseddf.query( 'run==%d & subrun1==%d & subrun2==%d'%(run,subrun1,subrun2) )
        if len(pulsed)==0:
            print "Not found: %d, %d, %d. Skipping."%(run,subrun1,subrun2)
            continue
        if os.path.exists( npfilename+'.npz') and remake==False:
            print "already made: ",npfilename
            npz = np.load( npfilename+'.npz' )
            arr = npz['wfmtree']
            outdf = pd.DataFrame( arr )
        else:
            outdf = process_run( run, subrun1, subrun2 )
            np.savez(npfilename,wfmtree=outdf.to_records())
            print (pulsed['pulsed_crate'].values[0],pulsed['pulsed_slot'].values[0],pulsed['pulsed_femch'].values[0])
        get_statistics( outdf, 5.0, 0.007, (pulsed['pulsed_crate'].values[0],pulsed['pulsed_slot'].values[0],pulsed['pulsed_femch'].values[0]), 
                        ref_channel=(pulsed['ref_crate'].values[0],pulsed['ref_slot'].values[0],pulsed['ref_femch'].values[0]), 
                        outfile='output_crosstalk/stats/run%03d_subrun%03d_%03d.stats'%(run,subrun1,subrun2) )


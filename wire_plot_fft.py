import os,sys
sys.path.append("/Users/twongjirad/working/uboone/vireviewer")
from vireviewer import getmw
import numpy as np
import pandas as pd
from channelmap import getChannelMap
from hoot import gethootdb
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import math

def get_pulsed_list(run):
    f = open('runmeta/run%03d_pulsed_ch.txt'%(run),'r')
    lines = f.readlines()
    pulsed_dict = {}
    for l in lines:
        data = l.strip().split()
        subrun1 = int(data[0])
        subrun2 = int(data[1])
        crate = int(data[2])
        slot = int(data[3])
        femch = int(data[4])
        if (subrun1,subrun2) not in pulsed_dict:
            pulsed_dict[(subrun1,subrun2)] = []
        pulsed_dict[(subrun1,subrun2)].append( [crate,slot,femch] )
    return pulsed_dict
    

def plot_run( mw, run, subrun1, subrun2, plotfft=True, subbg=True ):
    pulsed_list = get_pulsed_list(run)[(subrun1,subrun2)]
    print pulsed_list

    # loading in noise data
    if subbg==True:
        bgzp = np.load( 'output/run%03d_subrun%03d_%03d.npz'%(95,0,19) )
        bgarr = bgzp['wffftrgba']
        bgdf = pd.DataFrame( bgarr )
        bgdf.drop( 'index', axis=1, inplace=True )
    
        # changing column names
        bg_cols = []
        for col in bgdf.columns:
            if col not in ['crate','slot','femch']:
                col = "bg_"+col
            bg_cols.append( col )
        bgdf.columns = bg_cols

    # open data we are focuing on
    npzfile = np.load( 'output/run%03d_subrun%03d_%03d.npz'%(run,subrun1,subrun2) )
    arr = npzfile['wffftrgba']
    df = pd.DataFrame( arr )
    df.drop( 'index', axis=1, inplace=True )
    if subbg:
        df.set_index(['crate','slot','femch'],inplace=True)
        bgdf.set_index(['crate','slot','femch'],inplace=True)
        df = df.join( bgdf )

    hootdb = gethootdb()
    chmap = getChannelMap()
    hootdb.set_index( ['crate','slot','femch'], inplace=True )
    df = df.join( hootdb ).reset_index()

    # now have supertable
    print df.columns
    print len(df)
    print len(chmap)

    maxamp = np.max( df['max_amp'].values )
    arr = df.to_records()

    print pulsed_list[0]
    pulsed_row = df.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(pulsed_list[0][0], pulsed_list[0][1],pulsed_list[0][2]) )
    max_ampratio = pulsed_row['max_amp'].values[0]/pulsed_row['ped_rms'].values[0]
    pulsed_maxamp = pulsed_row['max_amp'].values[0]
    print "maxamp (overall): ",maxamp
    print "pulsed maxamp: ",pulsed_maxamp

    ampratio = np.zeros( len(df['max_amp'].values) )
    ampratio[:] = df['max_smooth'].values[:]
    ampratio[:] /= df['rms_smooth'].values[:]
    max_smooth = pulsed_row['max_smooth'].values[0]
    max_smooth_ratio = pulsed_row['max_smooth'].values[0]/pulsed_row['rms_smooth'].values[0]

    rmax = pulsed_row['rval'].values[0]
    gmax = pulsed_row['gval'].values[0]
    bmax = pulsed_row['bval'].values[0]

    rmax = 5000.0
    gmax = 3000.0
    bmax = 1000.0

    rgbmax = max( (rmax,gmax,bmax) )
    print "RGB Max: ",rmax,gmax,bmax,rgbmax

    bg_rmax = np.max( df['bg_rval'].values )
    bg_gmax = np.max( df['bg_gval'].values )
    bg_bmax = np.max( df['bg_bval'].values )

    candidates = []

    for r in arr:

        if math.isnan(r['wireid']):
            #print "skipping: ",r['crate'],r['slot'],r['femch']
            mw.vires.setWireColorByCSF( r['crate'],r['slot'],r['femch'], (0.01, 0.01, 0.01, 0.01) )
            continue

        pulsed = False
        if [r['crate'],r['slot'],r['femch']] in pulsed_list:
            pulsed = True

        # hack to fix unknown problem
        if (r['crate'],r['slot'],r['femch'])==(1,8,0):
            #mw.vires.setWireColorByCSF( r['crate'],r['slot'],r['femch'], (0.01, 0.01, 0.01, 0.01) )
            mw.vires.setWireColor( 'U',640, (0.01, 0.01, 0.01, 0.05) )
            continue
            
        alpha = 0.95

        # FFT
        if plotfft:
            red = r['rval']
            g = r['gval']
            b = r['bval']
            if subbg:
                red -= r['bg_rval']
                g -= r['bg_gval']
                b -= r['bg_bval']

            if red<0:
                red = 0
            if g<0:
                g = 0
            if b<0:
                b = 0
            red /= rmax
            g /= gmax
            b /= bmax

            if red>0.1 or g>0.1 or b>0.1 or pulsed:
                alpha = 0.8
                if subbg:
                    print r['crate'],r['slot'],r['femch'],r['plane'],int(r['wireid']),red,g,b,"bg=(",r['bg_rval']/rmax,r['bg_gval']/gmax,r['bg_bval']/bmax,")"
                else:
                    print r['crate'],r['slot'],r['femch'],r['plane'],['wireid'],red,g,b
                candidates.append( (r['crate'],r['slot'],r['femch']) )
            # pulsed wire color
            #if (r['crate'],r['slot'],r['femch'])==(6,9,0):
            #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 1.0 ) )

            #if above_thresh:
            mw.vires.setWireColor( r['plane'], int(r['wireid']), ( (0.1+red), (0.1+g), (0.1+b), alpha ) )

        # AMP
        else:
            red = 0.01 + 0.99*r['max_amp']/pulsed_maxamp
            if not pulsed:
                if r['max_smooth']/r['rms_smooth']>5.0 and r['max_amp']>1.0:
                    #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( red, 0.01, 0.01, alpha ) ) 
                    mw.vires.setWireColorByCSF( int(r['crate']),int(r['slot']),int(r['femch']), ( red, 0.01, 0.01, alpha ) ) 
                    print r['crate'],r['slot'],r['femch'],r['plane'],int(r['wireid']),red,r['max_amp'],pulsed
                else:
                    mw.vires.setWireColorByCSF( int(r['crate']),int(r['slot']),int(r['femch']), ( 0.01, 0.01, 0.01, alpha ) ) 
                    #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( 0.01, 0.01, 0.01, alpha ) ) 
            else:
                print "Pulsed: ",int(r['crate']),int(r['slot']),int(r['femch'])
                mw.vires.setWireColorByCSF( int(r['crate']),int(r['slot']),int(r['femch']), ( red, red, red, 1.0 ) )
                #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( red, red, red, 1.0 ) ) 
    print candidates
mw = getmw()
mw.vires.show()

if __name__ == "__main__":
    mw = getmw()
    plot_run( mw, 95, 44, 55 )
    #plot_run( mw, 83, 0, 0 )
    #plot_run( mw, 83, 0, 0 )
    mw.vires.show()
    #if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):                                                                                                                           
    pg.QtGui.QApplication.exec_()  
    raw_input()

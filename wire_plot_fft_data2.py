import os,sys
sys.path.append("/Users/twongjirad/working/uboone/vireviewer")
from vireviewer import getmw
import numpy as np
import pandas as pd
from hoot import gethootdb
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import math

from pulsed_list import get_pulsed_channel_list

def plot_run( mw, run, subrun1, subrun2, plotfft=True, subbg=True ):
    # load pulsed list
    pulseddf = get_pulsed_channel_list()
    pulseddf.set_index(['run','subrun1','subrun2'],inplace=True )
    try:
        pulsed = pulseddf.loc[run,subrun1,subrun2]
    except:
        print "Error with ",run,subrun1,subrun2,". No entry in pulsed list"
        return

    # loading in noise data
    if subbg==True:
        print "Loading background info from 95, 0, 19"
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
    npzfile = np.load( 'output_crosstalk/numpy/run%03d_subrun%03d_%03d.npz'%(run,subrun1,subrun2) )
    arr = npzfile['wfmtree']
    df = pd.DataFrame( arr )
    df.drop( 'index', axis=1, inplace=True )
    if subbg:
        print "merging background table"
        df.set_index(['crate','slot','femch'],inplace=True)
        bgdf.set_index(['crate','slot','femch'],inplace=True)
        df = df.join( bgdf )
    # now have supertable, indexed by crate,slot,femch
    print df.columns
    
    # get pulsed amp and reference amplitude
    pulsed_amp = df.loc[pulsed['pulsed_crate'],pulsed['pulsed_slot'],pulsed['pulsed_femch']]['wfamp']
    ref_amp = df.loc[pulsed['ref_crate'],pulsed['ref_slot'],pulsed['ref_femch']]['wfamp']
    print "Pulsed amp: ",pulsed_amp
    print "Referenced amp: ",ref_amp

    # get record array
    arr = df.to_records()

    # get r,g,b max relative to reference
    rmax = df.loc[pulsed['ref_crate'],pulsed['ref_slot'],pulsed['ref_femch']]['rval']
    gmax = df.loc[pulsed['ref_crate'],pulsed['ref_slot'],pulsed['ref_femch']]['gval']
    bmax = df.loc[pulsed['ref_crate'],pulsed['ref_slot'],pulsed['ref_femch']]['bval']

    rgbmax = max( (rmax,gmax,bmax) )
    print "RGB Max: ",rmax,gmax,bmax,"rgbmax=",rgbmax

    bg_rmax = np.max( df['bg_rval'].values )
    bg_gmax = np.max( df['bg_gval'].values )
    bg_bmax = np.max( df['bg_bval'].values )

    candidates = []

    for index,r in df.iterrows():
        if math.isnan(r['wireid']):
            print "skipping NAN wire: ",index
            mw.vires.setWireColorByCSF( index[0],index[1], index[2], (0.01, 0.01, 0.01, 0.01) )
            continue

        if index == (pulsed['pulsed_crate'],pulsed['pulsed_slot'],pulsed['pulsed_femch']):
            print "PULSED"
            pulsedch = True
        else:
            pulsedch = False

        if index == (pulsed['ref_crate'],pulsed['ref_slot'],pulsed['ref_femch']):
            print "REF"
            refch = True
        else:
            refch = False

        # hack to fix unknown problem
        if index==(1,8,0):
            print '(1,8,0) hack'
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

            if red>0.1 or g>0.1 or b>0.1 or pulsedch:
                alpha = 0.8
                if subbg:
                    print index[0],index[1],index[2],r['plane'],int(r['wireid']),red,g,b,"bg=(",r['bg_rval']/rmax,r['bg_gval']/gmax,r['bg_bval']/bmax,")"
                else:
                    print index[0],index[1],index[2],r['plane'],['wireid'],red,g,b
                candidates.append( (index[0],index[1],index[2]) )
            # pulsed wire color
            #if (index[0],index[1],index[2])==(6,9,0):
            #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 1.0 ) )

            #if above_thresh:
            mw.vires.setWireColor( r['plane'], int(r['wireid']), ( (0.1+red), (0.1+g), (0.1+b), alpha ) )

        # AMP
        else:
            red = 0.01 + 0.99*r['wfamp']/ref_amp
            if not pulsedch:
                if r['amp_ratio']>5.0 and r['wfamp']>7.0:
                    #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( red, 0.01, 0.01, alpha ) ) 
                    mw.vires.setWireColorByCSF( index[0],index[1],index[2], ( red, 0.01, 0.01, alpha ) ) 
                    #mw.vires.setWireColor( r['plane'], r['wireid'], ( red, 0.01, 0.01, alpha ) ) 
                    print index[0],index[1],index[2],r['plane'],int(r['wireid']),red,r['wfamp'],pulsedch
                else:
                    mw.vires.setWireColorByCSF( index[0],index[1],index[2], ( 0.01, 0.01, 0.01, alpha ) ) 
                    #mw.vires.setWireColor( r['plane'], r['wireid'], ( 0.01, 0.01, 0.01, alpha ) ) 
                    #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( 0.01, 0.01, 0.01, alpha ) ) 
            else:
                print "Pulsed: ",index
                #mw.vires.setWireColor( r['plane'], r['wireid'], ( red, red, red, 1.0 ) )
                mw.vires.setWireColorByCSF( index[0],index[1],index[2], ( red, red, red, 1.0 ) )
                #mw.vires.setWireColor( r['plane'], int(r['wireid']), ( red, red, red, 1.0 ) ) 
            if refch and not pulsedch:
                print "Reference channel: ",index
                mw.vires.setWireColorByCSF( index[0],index[1],index[2], ( 0, 1.0, 0.0, 1.0 ) )
    print "saving"
    mw.vires.show()
    mw.vires.paintGL()
    mw.vires.save('output_crosstalk/png/run%03d_subrun%03d_%03d.png'%(run,subrun1,subrun2))
    print candidates
mw = getmw()
mw.vires.show()
mw.vires.collapseWires()

def plot_all_runs():
    mw.vires.resetWireColors()
    data_files = os.listdir("data2")
    for data in data_files:
        if ".root" not in data:
            continue
        print data
        parts = data[:-len(".root")].split("_")
        run = int(parts[1][len("run"):])
        subrun1 = int(parts[2][len("subrun"):])
        subrun2 = int(parts[3])
        plot_run(mw,run,subrun1,subrun2,plotfft=False)
        
if __name__ == "__main__":
    mw = getmw()

    plot_run( mw, 95, 44, 55 )
    mw.vires.show()
    pg.QtGui.QApplication.exec_()  
    raw_input()

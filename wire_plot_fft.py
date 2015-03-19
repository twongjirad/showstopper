import os,sys
sys.path.append("/Users/twongjirad/working/uboone/vireviewer")
from vireviewer import getmw
import numpy as np
import pandas as pd
from channelmap import getChannelMap
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

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
        gbgdf = bgdf.groupby( ('crate','slot','femch') )
        bgdf2 = pd.DataFrame( gbgdf.mean() )

    # open data we are focuing on
    npzfile = np.load( 'output/run%03d_subrun%03d_%03d.npz'%(run,subrun1,subrun2) )
    arr = npzfile['wffftrgba']
    df = pd.DataFrame( arr )
    df.drop( 'index', axis=1, inplace=True )
    if subbg:
        gdf = df.groupby( ('crate','slot','femch') )
        df2 = pd.DataFrame( gdf.mean() )

        # join the data table
        df = df2.join( bgdf2 ).reset_index()

    arr = df.to_records()

    maxamp = np.max( df['max_amp'].values )
    print "maxamp: ",maxamp
    chmap = getChannelMap()
    print pulsed_list[0]
    pulsed_row = df.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(pulsed_list[0][0], pulsed_list[0][1],pulsed_list[0][2]) )

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
        row = chmap.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(r['crate'],r['slot'],r['femch']) )

        pulsed = False
        if [r['crate'],r['slot'],r['femch']] in pulsed_list:
            pulsed = True
        alpha = 0.8

        if len(row)>0:
            wireid = row['wireid'].values[0]
            plane = row['plane'].values[0]
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
                #else:
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 0.1 ) )
                if red>0.1 or g>0.1 or b>0.1 or pulsed:
                    alpha = 0.8
                    if subbg:
                        print r['crate'],r['slot'],r['femch'],plane,wireid,red,g,b,"bg=(",r['bg_rval']/rmax,r['bg_gval']/gmax,r['bg_bval']/bmax,")"
                    else:
                        print r['crate'],r['slot'],r['femch'],plane,wireid,red,g,b
                    candidates.append( (r['crate'],r['slot'],r['femch']) )
                # pulsed wire color
                #if (r['crate'],r['slot'],r['femch'])==(6,9,0):
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 1.0 ) )

                #if above_thresh:
                mw.vires.setWireColor( plane, wireid, ( (0.1+red), (0.1+g), (0.1+b), alpha ) )

            # AMP
            else:
                #if ( r['max_amp']>10.0 ):
                #    mw.vires.setWireColor( plane, wireid, ( 0.1 + 0.9*r['max_amp']/maxamp, 0.0, 0.0, 1.0 ) )
                #else:
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 0.1 ) )
                red = 0.05 + 0.95*r['max_amp']/maxamp
                if not pulsed:
                    mw.vires.setWireColor( plane, wireid, ( red, 0.05, 0.05, alpha ) ) 
                else:
                    mw.vires.setWireColor( plane, wireid, ( red, red, red, 1.0 ) ) 
                if red>0.15:
                    print r['crate'],r['slot'],r['femch'],plane,wireid,red,pulsed

                # pulsed wire color
                #if (r['crate'],r['slot'],r['femch'])==(6,9,0):
                #    mw.vires.setWireColor( plane, wireid, ( 0.0, 1.0, 0.0, 1.0 ) )
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

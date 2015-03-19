import os,sys
sys.path.append("/Users/twongjirad/working/uboone/vireviewer")
from vireviewer import getmw
import numpy as np
import pandas as pd
from channelmap import getChannelMap
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

def plot_run( mw, run, subrun1, subrun2, plotfft=True ):
    # loading in noise data
    bgzp = np.load( 'output/run%03d_subrun%03d_%03d.npz'%(95,27,36) )
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
    gdf = df.groupby( ('crate','slot','femch') )
    df2 = pd.DataFrame( gdf.mean() )

    # join the data table
    #df.join( bgdf, on=[('crate','slot','femch')] )
    df = df2.join( bgdf2 ).reset_index()

    arr = df.to_records()

    maxamp = 2000.0
    print "maxamp: ",maxamp
    chmap = getChannelMap()
    for r in arr:
        row = chmap.query( '(crate==%d) & (slot==%d) & (femch==%d)'%(r['crate'],r['slot'],r['femch']) )
        if len(row)>0:
            wireid = row['wireid'].values[0]
            plane = row['plane'].values[0]
            # FFT
            if plotfft:
                red = r['rval']-1.2*r['bg_rval']
                g = r['gval']-1.2*r['bg_gval']
                b = r['bval']-1.2*r['bg_bval']
                if red<0:
                    red = 0
                if g<0:
                    g = 0
                if b<0:
                    b = 0

                #if above_thresh:
                mw.vires.setWireColor( plane, wireid, ( 0.05+red, 0.05+g, 0.05+b, 1.0 ) )
                #else:
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 0.1 ) )
                if red>0.05 or g>0.05 or b>0.05:
                    print r['crate'],r['slot'],r['femch'],plane,wireid,red,g,b
                # pulsed wire color
                #if (r['crate'],r['slot'],r['femch'])==(6,9,0):
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 1.0 ) )
            # AMP
            else:
                #if ( r['max_amp']>10.0 ):
                #    mw.vires.setWireColor( plane, wireid, ( 0.1 + 0.9*r['max_amp']/maxamp, 0.0, 0.0, 1.0 ) )
                #else:
                #    mw.vires.setWireColor( plane, wireid, ( 1.0, 1.0, 1.0, 0.1 ) )
                mw.vires.setWireColor( plane, wireid, ( 0.05 + 0.95*r['max_amp']/maxamp, 0.05, 0.05, 1.0 ) ) 
                print r['crate'],r['slot'],r['femch'],plane,wireid,r['max_amp']

                # pulsed wire color
                #if (r['crate'],r['slot'],r['femch'])==(6,9,0):
                #    mw.vires.setWireColor( plane, wireid, ( 0.0, 1.0, 0.0, 1.0 ) )


if __name__ == "__main__":
    mw = getmw()
    plot_run( mw, 95, 44, 55 )
    #plot_run( mw, 83, 0, 0 )
    #plot_run( mw, 83, 0, 0 )
    mw.show()
    #if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):                                                                                                                           
    pg.QtGui.QApplication.exec_()  
    raw_input()

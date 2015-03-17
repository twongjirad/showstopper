import os,sys
import pyqtgraph

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from badchtable import get_badchtable

def get_index( crate, slot, femch ):
    index = crate*64*15 + (slot-4)*64 + femch
    return index
def get_triple(index):
    crate = int(index/(64*15))
    slot  = int((index-crate*64*15)/64)+4
    femch = int( (index-crate*64*15-(slot-4)*64 ) )
    return crate,slot,femch

badch = get_badchtable()
badch_list = badch[['Crate','Slot','FEM Channel']].values.tolist()
badch_indices = []
for (crate,slot,femch) in badch_list:
    badch_indices.append( get_index(crate,slot,femch) )
print "BADCHs: ",len(badch_indices)

center_wire = get_index( 2, 6, 0 )
good_indices = range(center_wire-32,center_wire+33)

# data                         
filename = "covamp_run083.npz"
datafile = np.load(filename)
data = datafile['mat']
use_subregion  = True
use_pyqtgraph = True
use_pyroot = True

app = QtGui.QApplication([])

if use_subregion:
    subset_indices = badch_indices+good_indices
    #subset_indices = badch_indices
    print "getting subset"
    subset = np.zeros( (len(subset_indices), len(subset_indices)) )
    for n,i in enumerate(subset_indices):
        for m,j in enumerate(subset_indices):
            subset[n,m] = data[i,j]
else:
    subset = data

if use_pyqtgraph:
    print "potting"
    w = pg.GraphicsLayoutWidget()
    maxadc_plot = w.addPlot( labels={"left":"unpulsed channel ID", "bottom":"pulsed channel ID"} )
    maxadc_image = pg.ImageItem( )
    maxadc_plot.addItem( maxadc_image )
    maxadc_image.setImage( subset )

    hist = pg.HistogramLUTItem()
    hist.setImageItem( maxadc_image )
    w.addItem(hist)

    w.show()

if use_pyroot:
    import ROOT as rt
    rt.gStyle.SetOptStat(0)
    rt.gStyle.SetPadLeftMargin(0.10)
    rt.gStyle.SetPadBottomMargin(0.10)
    rt.gStyle.SetPadTopMargin(0.01)
    rt.gStyle.SetPadRightMargin(0.10)

    n = len(subset_indices)
    print n

    c = rt.TCanvas("c","",1400,1400)
    c.Draw()
    hp =rt.TH1D('hp','Diagonal',n,0,n)
    h =rt.TH2D('h','',n,0,n,n,0,n)
    for x in xrange(0,subset.shape[0]):
        hp.SetBinContent( x+1, subset[x,x] )
        for y in xrange(0,subset.shape[1]):
            h.SetBinContent( x+1, y+1, subset[x,y] )

    for x in xrange(0,n):
        cr,s,f = get_triple( subset_indices[x] )
        h.GetXaxis().SetBinLabel(x+1, "[ %d, %d, %d ]"%(cr,s,f) )
        hp.GetXaxis().SetBinLabel(x+1, "[ %d, %d, %d ]"%(cr,s,f) )
        h.GetYaxis().SetBinLabel(x+1,"[ %d, %d, %d ]"%(cr,s,f) )
    h.GetXaxis().SetLabelSize(0.015)
    h.GetYaxis().SetLabelSize(0.015)
    h.Draw("COLZ")
    c.Update()

    cp = rt.TCanvas("cp","",1400,600)
    cp.Draw()
    hp.Draw()
    cp.Update()

raw_input()

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

badch = get_badchtable()
badch_list = badch[['Crate','Slot','FEM Channel']].values.tolist()
badch_indices = []
for (crate,slot,femch) in badch_list:
    badch_indices.append( get_index(crate,slot,femch) )
print "BADCHs: ",len(badch_indices)

good_indices = range(2000, 2500)

# data                                                                                                                                                                                        
datafile = open('maxadc.npy')
data = np.load( datafile )

app = QtGui.QApplication([])

subset_indices = badch_indices+good_indices
subset = np.zeros( (len(subset_indices), len(subset_indices)) )

print "getting subset"
for n,i in enumerate(subset_indices):
    for m,j in enumerate(subset_indices):
        subset[n,m] = data[i,j]
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

# import ROOT as rt
# c = rt.TCanvas("c","",800,600)
# c.Draw()
# h =rt.TH2D('h','',9600,0,9600,9600,0,9600)
# for x in xrange(0,data.shape[0]):
#     for y in xrange(0,data.shape[1]):
#         h.SetBinContent( x+1, y+1, data[x,y] )
#         #if y%1000==0:
#         #    print "y: ",y
#     if x%100==0:
#         print "x: ",x

# h.Draw("COLZ")
# c.Update()

raw_input()

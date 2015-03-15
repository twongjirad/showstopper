import os,sys
import pyqtgraph

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np

# data                                                                                                                                                                                        
datafile = open('maxadc.npy')
data = np.load( datafile )

app = QtGui.QApplication([])

w = pg.GraphicsLayoutWidget()
maxadc_plot = w.addPlot()
maxadc_image = pg.ImageItem()
maxadc_plot.addItem( maxadc_image )
maxadc_image.setImage( data )

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

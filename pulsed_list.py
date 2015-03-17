import os,sys
import numpy as np
import pandas as pd

def get_pulsed_channel_list( run ):
    filename = 'runmeta/run0%d_pulsed_ch.txt'%(run)
    mydata = np.genfromtxt( filename, dtype=np.int )
    return pd.DataFrame( mydata, columns=['crate','slot','femch'] )
    
        

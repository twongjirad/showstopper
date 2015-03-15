import os,sys
import pandas as pd

def get_badchtable():
    f = open('bad_channel_table.txt')
    badch = pd.read_csv( open('bad_channel_table.txt') )
    return badch

if __name__ == "__main__":
    print get_badchtable()
    


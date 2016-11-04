#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 16:39:23 2016

@author: alex
"""

import sys

if __name__ == "__main__":
    if len (sys.argv) <= 1:
        print ("Hello, world!")
    else:
        G4Run = sys.argv[2]
        # G4Run='0'
        print ("Starting Run#{}!".format (G4Run))

        import numpy as np
        import pandas as pd

        #        import os
        #        print(os.getcwd())

        pathSrcData = sys.argv[1]

        # pathSrcData = '/home/alex/Eclipse/TrAn test/' # data from GEANT4 here
        # pathSrcData ='/home/alex/Eclipse/Track analysis 2/'

        srcPrefix='microelectronics_nt_microelectronics_t'

        chunksize = 2**20
        DType = {'prt': np.int8, 'prc': np.int8, 'tID':np.int32,
                 'pID':np.int32,
                 'x1':np.float32, 'y1':np.float32, 'z1':np.float32,
                 'dEk':np.float32, 'PreEk':np.float32,
                 'x2':np.float32, 'y2':np.float32, 'z2':np.float32}
        Names = ['prt','prc', 'tID',
                 'pID', 'x1', 'y1', 'z1',
                 'dEk', 'PreEk',
                 'x2', 'y2', 'z2']

        df = pd.DataFrame(columns=Names) # create empty DataFrame to fill with tracks in loop
        trackN = 0 # track counter
        chunkN = 0 # chunk counter

        trackIndx = []

        reader = pd.read_table(pathSrcData + srcPrefix + G4Run +'.csv',
                               comment='#',header=None, chunksize=chunksize,
                               sep=',',engine='c',dtype=DType,names=Names)
        #generator = (chunk for chunk in reader)
        for chunk in reader:
            # добавляем chunk в DF в цикле, проводим анализ
            #chunkL = list(next(generator) for _ in range(1))
            #chunk = chunkL[0] # get chunk
            # print(chunk['tID'])

            df = df.append(chunk, ignore_index = True) # add chunk to df
            # print(df['tID'])
            # print((df['tID']).diff())

            # got indexes of track begins
            trBeg = (df['tID']==1) & ((df['tID']).diff()<0)
            idx = df[trBeg].index.tolist()

            print('chunk:%i \ttracks:%i' %(chunkN,len(idx)))
            trackN = trackN + len(idx)
            j = 0
            for i in idx:
                trackIndx.append(i-j) # got track length
                j = i # to make diff
            df = df[idx[-1]:] # remainder chunk
            chunkN = chunkN+1

        print('Done tracks search, total tracks: %i'%(trackN))

        print('Start splitting G4 csv..')
        Lines = ''
        for n in trackIndx:
            Lines = Lines + ' %i' % (n)
        BashFile = 'SplitR'+G4Run

        try:
            pathSave = sys.argv[3] +'Run'+ G4Run
        except:
            pathSave = pathSrcData +'Run'+ G4Run

        with open(BashFile, "w") as file:
            file.write('#!/bin/bash\n')
            file.write('rm -r -f ' + pathSave + '\n')
            file.write('mkdir -p ' + pathSave + '\n')
            file.write('{\n')
            file.write('\thead -n 15 > "'+ pathSave +'/hdr.txt"\n') # no header
            file.write('\ti=0\n')
            file.write('\tfor n in' + Lines + '\n')
            file.write('\tdo\n')
            file.write('\t\thead -n $n > "' + pathSave + '/tr$i.csv"\n')
            file.write('\t\tlet i++\n')
            file.write('\tdone\n')
            file.write('\tcat > ' + pathSave + '/tr$i.csv\n')
            file.write('} < "'+ pathSrcData + srcPrefix + G4Run +'.csv"')

        import os
        os.system('chmod u+x ' + BashFile)
        os.system('./'+BashFile)
        print('all done.')
#==============================================================================
#     import csv
#     with open(pathMatDataPrefix+'indx'+ G4Run +'.csv', "w") as output:
#         writer = csv.writer(output, lineterminator='\n')
#         #i = 0
#         #writer.writerow([i])
#         for val in trackIndx:
#             #i=i+val #cumsum
#             writer.writerow([val])
#==============================================================================
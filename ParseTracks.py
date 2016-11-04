#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 16:39:23 2016
Read track, correcting dEk, del points outside Target,
save csv:
dEk,x,y,z only
@author: alex
"""

import sys
import os
import numpy as np
import pandas as pd
import glob
import pickle
# http://stackoverflow.com/questions/4529815/saving-an-object-data-persistence-in-python


class SetupMesh:
    def __init__(self, Target, nbins=10):
        self.x = np.linspace(Target.xmin, Target.xmax,nbins)
        self.y = np.linspace(Target.ymin, Target.zmax,nbins)
        self.z = np.linspace(Target.zmin, Target.zmax,nbins)
        self.X, self.Y, self.Z = np.meshgrid(self.x,self.y,self.z)

        self.M = np.zeros(self.X.shape)
        self.E = np.zeros(self.X.shape)
        self.Ein = 0  # betaelectron energy counter

class SetupTarget:
    def __init__(self, geom):
        #        self.xmin = -float('Inf')
        #        self.xmax = float('Inf')
        #        self.ymin = -float('Inf')
        #        self.ymax = float('Inf')
        #        self.zmin = -float('Inf')
        #        self.zmax = float('Inf')

        if geom == 'flat':
            NiLayerThickness = 0.7*1e3
            SiO2LayerThickness = 0.14*1e3
            SiLayerThickness = 20*1e3

            tgSizeX = 100*1e3
            tgSizeY = 100*1e3
            wSizeZ = NiLayerThickness + SiO2LayerThickness \
                + SiLayerThickness
            tgCenterX = 0
            tgCenterY = 0
            tgCenterZ = -wSizeZ/2 + NiLayerThickness \
                + SiO2LayerThickness + SiLayerThickness/2
            tgSizeZ = SiLayerThickness
        else:
            raise ValueError('Undefined geometry: %s' %(geom))

        self.xmin = tgCenterX - tgSizeX/2
        self.xmax = tgCenterX + tgSizeX/2
        self.ymin = tgCenterY - tgSizeY/2
        self.ymax = tgCenterY + tgSizeY/2
        self.zmin = tgCenterZ - tgSizeZ/2
        self.zmax = tgCenterZ + tgSizeZ/2
def min0(x):
    if x<=0:
        return 0
    else:
        return x

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Hello, world!")
    else:
        G4Run = sys.argv[2]
        # G4Run='0'
        print("Starting Run#{}!".format(G4Run))

        DType = {'prt': np.int8, 'prc': np.int8, 'tID':np.int32,
                 'pID':np.int32,
                 'x1':np.float32, 'y1':np.float32, 'z1':np.float32,
                 'dEk':np.float32, 'PreEk':np.float32,
                 'x2':np.float32, 'y2':np.float32, 'z2':np.float32}
        Names = ['prt','prc', 'tID',
                 'pID', 'x1', 'y1', 'z1',
                 'dEk', 'PreEk',
                 'x2', 'y2', 'z2']
        # Processes from G4:
        prc = {'msc': 30,# "msc" 30
               'elastic': 21, #"e-_G4MicroElecElastic" 21
               'inelastic': 22, # "e-_G4MicroElecInelastic 22
               'capture': 11, # "eCapture" 11
               'eIoni': 40 # "eIoni"	40
               }

        Target = SetupTarget('flat')  # setup Target parameters
        mesh = SetupMesh(Target, nbins=sys.argv[3])
        # mesh = SetupMesh(Target,100)

        # pathSrcData = '/home/alex/Eclipse/Test/'+'Run'+G4Run+'/'
        pathSrcData = sys.argv[1]+'Run'+G4Run+'/'
        Files = glob.glob(pathSrcData+"*.csv")

        for file in Files:
            # file = Files[1]
            print(os.path.basename(file), end='')

            # Read track data, with all secondary e-
            tr = pd.read_table(file, comment='#', header=None,
                               sep=',', engine='c', dtype=DType, names=Names)
            mesh.Ein = mesh.Ein + tr['PreEk'][0]  # save primary e- energy
            # print(tr['TrackID'])

            # divide tracks to subtracks с учетом затрат энергии на их создание
            # убирает потери на создание
            # вторичного трека из потерь энергии родителя
            # ищем вершины вторичных треков, находим их на треках родителей, вычитаем
            # их начальную энергию из потерь родителей
            # search start point of track, remove starting energy
            # from pdrent track
            tIDs = tr['tID'].unique().tolist()
            # del '1' from track numbers
            tIDs.remove(1)

            for sec in tIDs:  # loop over only secondary e-
                # sec = tIDs[0]
                # start point index and coords
                idxStartPnt = np.where(tr['tID']==sec)[0][0]
                #& (tr['prc']==22)
                x1 = tr.ix[idxStartPnt]['x1']
                y1 = tr.ix[idxStartPnt]['y1']
                z1 = tr.ix[idxStartPnt]['z1']

                # tr.ix[idxStartPnt]
                ParentID = tr.ix[idxStartPnt]['pID']
                # get list of Parent track points
                Parent = tr[tr['tID'] == ParentID].index.tolist()

                # ищем точку на треке родителя с координатами вершины текущего трека
                m = ((tr.ix[Parent]['x2']-x1)**2
                    + (tr.ix[Parent]['y2']-y1)**2
                    + (tr.ix[Parent]['z2']-z1)**2)
                m = m[m < 1e-3].index.tolist()  # less than 1e-3 nm
                if len(m)>1:
                    df = tr.ix[m]
                    m = df[df['prc'] == prc['inelastic']].index.tolist()
                #elif len(m)==0:
                #    pass
                    # raise ValueError('can not found track %i begin point' %(sec))
                    # !!! была ошибка, не находил трек. Руками проверил, его просто не было
                    # трек выглядел нормально в остальном. Глюк Geant4?
                # corrrecting dEk
                try:
                    m = m[0]
                    # tr.ix[[m-1, m, m+1]]['dEk']
                    dEk = tr.ix[m]['dEk']
                    PreEk = tr.ix[idxStartPnt]['PreEk']
                    tr.set_value(m, 'dEk', min0(dEk - PreEk))
                except:
                    pass

            # find points inside Target region
            InTarget = (tr['x1']>=Target.xmin) & \
                           (tr['x1']<=Target.xmax) & \
                           (tr['y1']>=Target.ymin) & \
                           (tr['y1']<=Target.ymax) & \
                           (tr['z1']>=Target.zmin) & \
                           (tr['z1']<=Target.zmax)
            # which have processes, able to generate EHP
            GenerateEhp = (tr['prc']==prc['inelastic']) | \
                    (tr['prc']==prc['capture']) |\
                    (tr['prc']==prc['eIoni'])

            tr = tr[InTarget & GenerateEhp]

            # calculate localization of EHP generation & its energy
            ix = np.digitize(np.array(tr.x1), mesh.x)
            iy = np.digitize(np.array(tr.y1), mesh.y)
            iz = np.digitize(np.array(tr.z1), mesh.z)
            dEk = np.array(tr.dEk)

            for i in range(len(ix)):
                mesh.E[ix[i]-1, iy[i]-1, iz[i]-1] = \
                    mesh.E[ix[i]-1, iy[i]-1, iz[i]-1] + dEk[i]
                mesh.M[ix[i]-1, iy[i]-1, iz[i]-1] = \
                    mesh.M[ix[i]-1, iy[i]-1, iz[i]-1] + 1
            print('.')

        # save mesh
        print('Done, saving mesh', end='')
        with open(pathSrcData+ 'meshR%s.pkl'%(G4Run), 'wb') as output:
            pickle.dump(mesh, output, pickle.HIGHEST_PROTOCOL)
        print('... done')
        print('Done run %s!'%(G4Run))



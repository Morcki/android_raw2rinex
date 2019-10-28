# -*- coding: utf-8 -*-
MAXDELPOSFORNAVM = 20 # maximum position can change on one iteration of 
# nav solution without los vector changing by more than 1 microradian
MAXPRRUNCMPS = 10 # max pseudorange rate (Doppler) uncertainty.
# bigger values may just be the search bin size, thus not valid for nav.
MAXTOWUNCNS = 500 # maximum Tow uncertainty, 500 ns. Satellite range 
# can change by about half a millimeter in this time
MINNUMGPSEPH = 24 # minimum number of GPS ephemeris considered OK
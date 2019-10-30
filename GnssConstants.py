# -*- coding: utf-8 -*-
EARTHECCEN2 = 6.69437999014e-3  # WGS 84 (Earth eccentricity)^2 (m^2)
EARTHMEANRADIUS = 6371009       # Mean R of ellipsoid(m) IU Gedosey& Geophysics
EARTHSEMIMAJOR = 6378137        # WGS 84 Earth semi-major axis (m)
EPHVALIDSECONDS = 7200          # +- 2 hours ephemeris validity
DAYSEC = 86400                  # number of seconds in a day
FREL = -4.442807633e-10         # Clock relativity parameter, (s/m^1/2)
GPSEPOCHJD = 2444244.5          # GPS Epoch in Julian Days
HORIZDEG = 5                    # angle above horizon at which GPS models break down
LIGHTSPEED = 2.99792458e8       # WGS-84 Speed of light in a vacuum (m/s)
# mean time of flight btwn closest GPS sat (~66 ms) & furthest (~84 ms):
MEANTFLIGHTSECONDS = 75e-3;
mu = 3.986005e14      # WGS-84 Universal gravitational parameter (m^3/sec^2)
WE = 7.2921151467e-5  # WGS 84 value of earth's rotation rate (rad/s)
WEEKSEC = 604800      # number of seconds in a week
MILLISEC = 10e8       # number of nano seconds in 100ms 
# frequency here
GPS_FREQ	= 10230000.0
GPS_L1	    = 154*GPS_FREQ
GPS_L2	    = 120*GPS_FREQ
GPS_L5	    = 115*GPS_FREQ

GLS_FREQ    = 178000000.0
GLS_L1      = 9*GLS_FREQ
GLS_L2      = 7*GLS_FREQ
GLS_dL1     = 562500.0
GLS_dL2     = 437500.0

GAL_E1      = GPS_L1
GAL_E5      = 1191795000.0
GAL_E5a     = GPS_L5
GAL_E5b     = 1207140000.0
GAL_E6      = 1278750000.0

BDS_B1      = 1561098000.0
BDS_B2      = 1207140000.0
BDS_B3      = 1268520000.0

QZS_L1      = GPS_L1
QZS_L2      = GPS_L2
QZS_L5      = GPS_L5
QZS_LEX     = 1278750000.0

SYS='GSRJCE'

MAXSAT = 50

GLS_IFREQ   = {
        1 :  1,
        2 : -4,
        3 :  5,
        4 :  6,
        5 :  1,
        6 : -4,
        7 :  5,
        8 :  6,
        9 : -2,
        10: -7,
        11:  0,
        12: -1,
        13: -2,
        14: -7,
        15:  0,
        16: -1,
        17:  4,
        18: -3,
        19:  3,
        20:  2,
        21:  4,
        22: -3,
        23:  3,
        24:  2,
        26: -5
        }
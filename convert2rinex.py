# -*- coding: utf-8 -*-
import numpy as np
import re
import GnssConstants
class Convert():
    def __init__(self,rfile,HeadInfor):
        self.rfile = rfile
        
        self.version = 3.03
        self.Marker  = "PyConverT"
        
        matchobj = re.search(r'(.*):',HeadInfor['Manufacturer'])
        self.toolType = matchobj.group(1).strip()
        matchobj = re.search(r':(.*)',HeadInfor['Manufacturer'])
        self.toolName = matchobj.group(1).strip()
        with open(self.rfile,'w') as f:
            f.writelines('')
#        with open(self.rfile,'r+') as f:
#            f.truncate()
    def addRinexHead(self,gnssMeas):
        rinexHead = ''
        utcTime = gnssMeas.GpsTime
        with open(self.rfile,'a+') as f:
            rinexHead += "     %3.2f           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE\n" % self.version
            rinexHead += "%-20s                    %4d%02d%02d %02d%02d%02d UTC PGM / RUN BY / DATE\n"  % (self.Marker,*utcTime)
            rinexHead += "PyConverT                                                   MARKER NAME\n"
            rinexHead += "GnssLogger                                                  MARKER TYPE\n" 
            rinexHead += "Logger              Logger                                  OBSERVER / AGENCY\n"
            rinexHead += "unknown             %-20s%-20sREC # / TYPE / VERS\n" % (self.toolType,self.toolName)
            rinexHead += "unknown             %-20s                    ANT # / TYPE\n"        % self.toolName
            rinexHead += "        0.0000        0.0000        0.0000                  APPROX POSITION XYZ\n"
            rinexHead += "        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N\n"
            rinexHead += "G    8 C1C L1C D1C S1C C5Q L5Q D5Q S5Q                      SYS / # / OBS TYPES\n"
            rinexHead += "R    4 C1C L1C D1C S1C                                      SYS / # / OBS TYPES\n"
            rinexHead += "E    8 C1C L1C D1C S1C C5Q L5Q D5Q S5Q                      SYS / # / OBS TYPES\n"
            rinexHead += "C    4 C2I L2I D2I S2I                                      SYS / # / OBS TYPES\n"
            rinexHead += "  %04d     %d    %d     %d    %d   %10.7f     %3s         TIME OF FIRST OBS\n"   % (*utcTime,'GPS')
            rinexHead += " 24 R01  1 R02 -4 R03  5 R04  6 R05  1 R06 -4 R07  5 R08  6 GLONASS SLOT / FRQ #\n"
            rinexHead += "    R09 -2 R10 -7 R11  0 R12 -1 R13 -2 R14 -7 R15  0 R16 -1 GLONASS SLOT / FRQ #\n"
            rinexHead += "    R17  4 R18 -3 R19  3 R20  2 R21  4 R22 -3 R23  3 R24  2 GLONASS SLOT / FRQ #\n"
            rinexHead += " C1C    0.000 C1P    0.000 C2C    0.000 C2P    0.000        GLONASS COD/PHS/BIS\n"
            rinexHead += "                                                            END OF HEADER\n"
            f.writelines(rinexHead)
            
    def _getSatData(self,svid,conType,meas,freqNum):
        oldConType = 0
        count = 0 # numbers of svid used in old system type
        oldsvid = []
        satData = []
        loc2save = lambda ifreq : 0 if ifreq == 1 else 1
        for i,isvid in enumerate(svid):
            if freqNum[i] == 0:
                satData.append([np.nan,np.nan])
                continue
            if conType[i] != oldConType:
                count += len(oldsvid)
                oldsvid = []
                oldConType = conType[i]
            if isvid in oldsvid:
                satData[count + oldsvid.index(isvid)][loc2save(freqNum[i])] = meas[i]
                continue
            oldsvid.append(isvid)
            satData.append([np.nan,np.nan])
            satData[-1][loc2save(freqNum[i])] = meas[i]
        return satData
    
    def _getSatInfor(self,svid,conType):
        self.Svid = []
        self.ConstellationType = []
        oldConType = -1
        for isvid,con in zip(svid,conType):
            if con != oldConType:
                oldSvid = []
            if (con == oldConType) and (isvid in oldSvid):
                continue
            else:
                oldSvid.append(isvid)
                oldConType = con
                self.Svid.append(isvid)
                self.ConstellationType.append(int(con)-1)
                
    def processGnssMeas(self,gnssMeas):
        self._getSatInfor(gnssMeas.Svid,gnssMeas.ConstellationType)
        
        self.PrM       = self._getSatData(gnssMeas.Svid,gnssMeas.ConstellationType,gnssMeas.PrM,gnssMeas.freqNum)
        self.PhaseMeas = self._getSatData(gnssMeas.Svid,gnssMeas.ConstellationType,gnssMeas.PhaseMeas,gnssMeas.freqNum)
        self.PrrMps    = self._getSatData(gnssMeas.Svid,gnssMeas.ConstellationType,gnssMeas.PrrMps,gnssMeas.freqNum)
        self.Cn0DbHz   = self._getSatData(gnssMeas.Svid,gnssMeas.ConstellationType,gnssMeas.Cn0DbHz,gnssMeas.freqNum)
        self.CarrierFrequencyHz = self._getSatData(gnssMeas.Svid,gnssMeas.ConstellationType,gnssMeas.CarrierFrequencyHz,gnssMeas.freqNum)
        
    def gnssmeas2rinex(self,gnssMeas):
#        nsat = len(gnssMean.Svid)
        # weekNum = np.floor(gnssMeas.FctSeconds / GnssConstants.WEEKSEC)
        snrComput = lambda prrMps,freq: prrMps * (-1) * freq / GnssConstants.LIGHTSPEED if (prrMps != 0) and (freq != 0) else 0
        self.processGnssMeas(gnssMeas)
        
        with open(self.rfile,'a+') as f:
            rinexText = ''
            nsat = len(self.Svid)
            nValidSat = nsat
            for isat in range(nsat):
                if np.all(np.isnan(np.array(self.PrM)[isat])) :
                    nValidSat -= 1
                    continue
                rinexText += "%s%02d%14.3f  %14.3f  %14.3f  %14.3f  %14.3f  %14.3f  %14.3f  %14.3f\n" % (
                        GnssConstants.SYS[self.ConstellationType[isat]],
                        self.Svid[isat],
                        self.PrM[isat][0],
                        self.PhaseMeas[isat][0],
                        snrComput(self.PrrMps[isat][0],self.CarrierFrequencyHz[isat][0]),
                        self.Cn0DbHz[isat][0],
                        self.PrM[isat][1],
                        self.PhaseMeas[isat][1],
                        snrComput(self.PrrMps[isat][1],self.CarrierFrequencyHz[isat][1]),
                        self.Cn0DbHz[isat][1]
                        )
            if nValidSat == 0:
                return None
            utcTime = gnssMeas.GpsTime
            rinexText = rinexText.replace('nan','   ')
            rinexText = "> %04d %02d %02d %02d %02d %10.7f%3d%3d\n" % (*utcTime,0,nValidSat) + rinexText
            f.writelines(rinexText)
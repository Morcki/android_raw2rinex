# -*- coding: utf-8 -*-
from itertools import islice
import numpy as np
class RawDataReader():
    sysType = [1,3,5,6]
    LogFile = './Log.txt'
    intType   = ['State','Svid','AccumulatedDeltaRangeState']
    int64Type = ['ElapsedRealtimeMillis','TimeNanos','FullBiasNanos','ReceivedSvTimeNanos','ReceivedSvTimeUncertaintyNanos']
    
    def __init__(self,raw_path,nHead,HeadInfor):
        self.nHead     = nHead
        self.raw_path  = raw_path
        self.HeadInfor = HeadInfor
        self.HeadIndex = {ihead:i for i,ihead in enumerate(self.HeadInfor['DataFormat'])}
        self.checkTime = -1
        self.epochData = []
        
    def _filterData(self,linelist):
        # choose GPS + GLS + GAL + BDS system
        if not linelist[self.HeadIndex['ConstellationType']] in RawDataReader.sysType:
            return None
        if not linelist[self.HeadIndex['Svid']] <= 50:
            return None
        if not (
                #(int(linelist[self.HeadIndex['State']]) & 2**0) * 
                ((int(linelist[self.HeadIndex['State']]) & 2**3) or 
                 #(int(linelist[self.HeadIndex['State']]) & 2**0) *
                 (int(linelist[self.HeadIndex['State']]) & 2**7))
                ):
            return None
        return linelist
            
    def _checkHeadInfor(self):
        sFail = ''
        if not "TimeNanos" in self.HeadInfor['DataFormat']:
            sFail += "TimeNanos missing from GnssLogger File.\n"
        if not "FullBiasNanos" in self.HeadInfor['DataFormat']:
            sFail += "FullBiasNanos missing from GnssLogger File.\n"
        print(sFail)
        with open(RawDataReader.LogFile,'a+') as f:
            f.writeline(sFail)
    def _convertType(self,no,x):
        if x.strip() == '':
            return None
        if self.HeadInfor['DataFormat'][no] in RawDataReader.int64Type:
            return np.int64(x)
            
        elif self.HeadInfor['DataFormat'][no] in RawDataReader.intType:
            return np.int(x)
        else:
            return np.float64(x)
    def _convertArrType(self,head,value):
        if head in RawDataReader.int64Type:
            value = np.array(value,dtype=np.int64)
        elif head in RawDataReader.intType:
            value = np.array(value,dtype=np.int)
        else:
            value = np.array(value,dtype=np.float64)
        return value
    def _checkRawLine(self,linetext):
        linelist = [self._convertType(no,i) for no,i in enumerate(linetext.split(','))]
        Rx = np.int64(linelist[self.HeadIndex['TimeNanos']] - linelist[self.HeadIndex['FullBiasNanos']]) * 1e-6
        linelist = self._filterData(linelist)
        if abs(Rx - self.checkTime) > 1 and self.checkTime != -1:
            self.checkTime = Rx
            return True,linelist
        else:
            self.checkTime = Rx
            return False,linelist
        
    def _saveEpochData(self,linelist,pick=False,gnssRaw=None):
        if pick:
            epochData = self.epochData[:]
            if not epochData:
                return None
            else:
                epochData = np.array(epochData)
                if linelist:
                    self.epochData = [linelist]
                else:
                    self.epochData = []
            gnssRaw.gnssRaw = {iHead:self._convertArrType(iHead,epochData[:,self.HeadIndex[iHead]]) for iHead in self.HeadInfor['DataFormat']}
            gnssRaw.rawLen = len(epochData)
            return 1
        else:
            if linelist:
                self.epochData.append(linelist)
            return None
        
    def _checkGnssClock(self,gnssRaw,rawLen):
        sFail = ''
        if not "BiasNanos" in self.HeadInfor['DataFormat']:
            gnssRaw['BiasNanos'] = np.zeros(rawLen)
        if not "TimeOffsetNanos" in self.HeadInfor['DataFormat']:
            gnssRaw['TimeOffsetNanos'] = np.zeros(rawLen)
        if not "HardwareClockDiscontinuityCount" in self.HeadInfor['DataFormat']:
            gnssRaw['HardwareClockDiscontinuityCount'] = np.zeros(rawLen)
            sFail += 'WARNING: Added HardwareClockDiscontinuityCount=0 because it is missing from GNSS Logger file\n'
        bChangeSign = np.any(gnssRaw['FullBiasNanos'] < 0) & np.any(gnssRaw['FullBiasNanos'] > 0)
        if bChangeSign:
            raise Exception("FullBiasNanos changes sign within log file, this should never happen")
        if np.any(gnssRaw['FullBiasNanos'] > 0):
            gnssRaw['FullBiasNanos'] *= -1
            sFail += "WARNING: FullBiasNanos wrong sign. Should be negative. Auto changing inside ReadGpsLogger\n"
            sFail += "FullBiasNanos wrong sign."
        # add allRxMillis field
        gnssRaw['allRxMillis'] = np.rint(1.0 * (gnssRaw['TimeNanos'] - gnssRaw['FullBiasNanos']) * 1e-6)
        print(sFail)
        with open(RawDataReader.LogFile,'a+') as f:
            f.writelines(sFail)
            
    def raw_epochstream(self,gnssRaw):
        gnssRaw.clear()
        with open(self.raw_path) as f:
            for i,iline in enumerate(islice(f,self.nHead,None),self.nHead):
                if not iline[:3].upper() == "RAW":
                    continue
                else:
                    ok,rawlinelist = self._checkRawLine(iline[4:])
                    if ok:
                        if self._saveEpochData(rawlinelist,pick=True,gnssRaw=gnssRaw):
                            self._checkGnssClock(gnssRaw.gnssRaw,gnssRaw.rawLen)
                            yield gnssRaw
                        else:
                            continue
                    else:
                        self._saveEpochData(rawlinelist)
        if self.epochData:
            self._saveEpochData(None,pick=True,gnssRaw=gnssRaw)
            self._checkGnssClock(gnssRaw.gnssRaw,gnssRaw.rawLen)
            yield gnssRaw
    def fix_epochstream(self,gpsLoc):
        with open(self.raw_path) as f:
            for i,iline in enumerate(islice(f,self.nHead,None),self.nHead):
                if not iline[:3].upper() == "FIX":
                    continue
                else:
                    fixline = iline[4:]
                    fixdata = [i for i in fixline.split(',')]
                    gpsLoc.loc2rfile(fixdata)
                    yield True
                    
                    
                
            
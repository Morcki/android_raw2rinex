# -*- coding: utf-8 -*-
import GnssThresholds
import GnssConstants
import numpy as np
import Time
class GnssRaw():
    def __init__(self):
        self._prepself()
        
    def clear(self):
        self._prepself()
        
    def _prepself(self):
        self._prepClock()
        self._prepMeas()
        self.gnssRaw = {}
        self.gnssRaw.update(self.gnssClockFields)
        self.gnssRaw.update(self.gnssMeasurementFields)
        
    def _prepClock(self):
        clockfields = ['TimeNanos',
                       'TimeUncertaintyNanos',
                       'LeapSecond',
                       'FullBiasNanos',
                       'BiasUncertaintyNanos',
                       'DriftNanosPerSecond',
                       'DriftUncertaintyNanosPerSecond',
                       'HardwareClockDiscontinuityCount',
                       'BiasNanos']
        self.gnssClockFields = {i:None for i in clockfields}
        
    def _prepMeas(self):
        measurementfields = ['Cn0DbHz',
                             'ConstellationType',
                             'MultipathIndicator',
                             'PseudorangeRateMetersPerSecond',
                             'PseudorangeRateUncertaintyMetersPerSecond',
                             'ReceivedSvTimeNanos',
                             'ReceivedSvTimeUncertaintyNanos',
                             'State',
                             'Svid',
                             'AccumulatedDeltaRangeMeters',
                             'AccumulatedDeltaRangeUncertaintyMeters',
                             'CarrierFrequencyHz']
        self.gnssMeasurementFields = {i:None for i in measurementfields}
        
class AdrMconstBias():
    timeLimit = 10 * 60
    sysType = [1,3,5,6]
    def __init__(self):
        '''
        checkCycleSlip:
            systerm: GPS GLS BDS GAL
                satNumber: 1-50
                    -1               Not initialized
                     0               valid data
                     1               cycle-slip
        '''
        self.checkTime = {isys : {isat : np.inf for isat in range(GnssConstants.MAXSAT)} for isys in AdrMconstBias.sysType}
        self.constBias = {isys : {isat : np.nan for isat in range(GnssConstants.MAXSAT)} for isys in AdrMconstBias.sysType}
        self.refPrM    = {isys : {isat : np.nan for isat in range(GnssConstants.MAXSAT)} for isys in AdrMconstBias.sysType}
        
        self.refClkDCount = 0
    @staticmethod
    def wavelength(ifreq,isys,isvd,freqv=None):
        if ifreq == 0:
            return np.nan
        if ifreq == 1 and isys == 1:
            return GnssConstants.LIGHTSPEED / GnssConstants.GPS_L1
        if ifreq != 1 and isys == 1:
            return GnssConstants.LIGHTSPEED / GnssConstants.GPS_L5
        if ifreq == 1 and isys == 3:
#            gls_freq = round((freqv - GnssConstants.GLS_L1) / GnssConstants.GLS_dL1) * GnssConstants.GLS_dL1 + GnssConstants.GLS_L1
            gls_freq = GnssConstants.GLS_L1 + GnssConstants.GLS_IFREQ[isvd] * GnssConstants.GLS_dL1
            return GnssConstants.LIGHTSPEED / gls_freq
        if ifreq != 1 and isys == 3:
            #gls_freq = round((freqv - GnssConstants.GLS_L2) / GnssConstants.GLS_dL2) * GnssConstants.GLS_dL2 + GnssConstants.GLS_L2
#            gls_freq = GnssConstants.GLS_L2 + GnssConstants.GLS_IFREQ[isvd] * GnssConstants.GLS_dL2
            return np.nan # GnssConstants.LIGHTSPEED / GnssConstants.GLS_L2
        if ifreq == 1 and isys == 5:
            return GnssConstants.LIGHTSPEED / GnssConstants.BDS_B1
        if ifreq != 1 and isys == 5:
            return GnssConstants.LIGHTSPEED / GnssConstants.BDS_B2
        if ifreq == 1 and isys == 6:
            return GnssConstants.LIGHTSPEED / GnssConstants.GAL_E1
        if ifreq != 1 and isys == 6:
            return GnssConstants.LIGHTSPEED / GnssConstants.GAL_E5a
    @staticmethod
    def getRealMeasWaveL(freqNum,conType,freqValue):
        return np.array([AdrMconstBias.wavelength(ifreq,isys,freqv) for ifreq,isys,freqv in zip(freqNum,conType,freqValue)])
    @staticmethod
    def getStandardWaveL(freqNum,conType,sVids):
        return np.array([AdrMconstBias.wavelength(ifreq,isys,isvd) for ifreq,isys,isvd in zip(freqNum,conType,sVids)])
    def getDelPr(self,gnssMeas):
        nmeas = len(gnssMeas.Svid)
        delPrM = []
        bClockDis = (gnssMeas.ClkDCount - self.refClkDCount) != 0
        self.refClkDCount = gnssMeas.ClkDCount
        for i in range(nmeas):
            isys = gnssMeas.ConstellationType[i]
            isvd = gnssMeas.Svid[i]
            if bClockDis or (self.refPrM[isys][isvd] == np.nan):
                self.refPrM[isys][isvd] = gnssMeas.PrM[i]
                delPrM.append(np.nan)
            else:
                delPrM.append(gnssMeas.PrM[i] - self.refPrM[isys][isvd])
        return np.array(delPrM)
        
    def processAdrM(self,gnssMeas):
        nmeas   = len(gnssMeas.Svid)
        waveLen = AdrMconstBias.getStandardWaveL(gnssMeas.freqNum,gnssMeas.ConstellationType,gnssMeas.CarrierFrequencyHz)
        constBias = []
        for i in range(nmeas):
            isys = gnssMeas.ConstellationType[i]
            isvd = gnssMeas.Svid[i]
            if (gnssMeas.AdrState[i] & 2**0): # Valid Adr Meas
                ltime = (gnssMeas.fctTime - self.checkTime[isys][isvd]) > AdrMconstBias.timeLimit
                # update time-tag
                self.checkTime[isys][isvd] = gnssMeas.fctTime
                # check if failed time-tag or no-valued Bias
                if ltime or np.isnan(self.constBias[isys][isvd]):
                    bias = gnssMeas.PrM[i] - gnssMeas.AdrM[i]
                    self.constBias[isys][isvd] = bias
                    constBias.append(bias)
                else:
                    constBias.append(self.constBias[isys][isvd])
            elif (gnssMeas.AdrState[i] & 2**4): # Cycle-slip Adr Meas
                # update time-tag
                self.checkTime[isys][isvd] = gnssMeas.fctTime
                bias = gnssMeas.PrM[i] - gnssMeas.AdrM[i]
                self.constBias[isys][isvd] = bias
                constBias.append(bias)
            else:
                if not np.isnan(self.constBias[isys][isvd]):
                    # delete time-tag
                    self.checkTime[isys][isvd] = np.inf
                    self.constBias[isys][isvd] = np.nan
                constBias.append(np.nan)
        return (gnssMeas.AdrM + np.array(constBias)) / waveLen
    
class GnssMeas():
    LogFile = './Log.txt'
    def __init__(self):
        self.iepoch = 1
        self.ConstComp = AdrMconstBias()
    
    def filterValid(self,gnssRaw):
        # remove fields corresponding to measurements that are invalid
        # check ReceivedSvTimeUncertaintyNanos, PseudorangeRateUncertaintyMetersPerSecond
        # for now keep only Svid with towUnc<0.5 microseconds and prrUnc < 10 mps
        sMsg = ''
        iTowUnc = gnssRaw['ReceivedSvTimeUncertaintyNanos'] > GnssThresholds.MAXTOWUNCNS
        iPrrUnc = gnssRaw['PseudorangeRateUncertaintyMetersPerSecond'] > GnssThresholds.MAXPRRUNCMPS
        
        iBad = iTowUnc | iPrrUnc
        if np.any(iBad):
            numBad = np.sum(iBad)
            if numBad >= len(iBad):
                raise Exception("Removing all measurements in gnssRaw.")
            gnssRaw = {i:gnssRaw[i][iBad==0] for i in gnssRaw.keys()}
            sMsg += 'Removed %d bad meas inside ProcessGnssMeas > FilterValid because:\n' % numBad
        if np.any(iTowUnc):
            sMsg += 'towUnc > %.0f ns\n' % GnssThresholds.MAXTOWUNCNS
        if np.any(iPrrUnc):
            sMsg += 'prrUnc > %.0f m/s\n' % GnssThresholds.MAXPRRUNCMPS
        print(sMsg)
        with open(GnssMeas.LogFile,'a+') as f:
            f.writelines(sMsg)
        return gnssRaw
    
    def checkGpsTimeRollover(self,tRxSecondes,prSeconds,Type):
        if Type == 'day':
            const_t = GnssConstants.DAYSEC
            iRollover = prSeconds > const_t / 2
        elif Type == 'week':
            const_t = GnssConstants.WEEKSEC
            iRollover = prSeconds > const_t / 2
        if np.any(iRollover):
            print('WARNING: %s rollover detected in time tags. Adjusting ...\n' % Type)
            prS = prSeconds[iRollover]
            delS = np.round(prS / const_t) * const_t
            prS -= delS
            maxBiasSeconds = 10
            if np.any(prS>maxBiasSeconds):
                raise Exception("Failed to correct %s rollover\n" % Type)
            else:
                prSeconds[iRollover] = prS
                tRxSecondes[iRollover] = tRxSecondes[iRollover] - delS
                print("Corrected %s rollover\n" % Type)
        prSeconds[tRxSecondes == 0] = np.nan
        return tRxSecondes,prSeconds
    
    
    def _getDelPrMinusAdrM(self):
        #/* However, it is expected that the data is only accurate when:
        # *  'accumulated delta range state' == GPS_ADR_STATE_VALID.
        #*/
        # define GPS_ADR_STATE_UNKNOWN                       0
        # define GPS_ADR_STATE_VALID                     (1<<0)
        # define GPS_ADR_STATE_RESET                     (1<<1)
        # define GPS_ADR_STATE_CYCLE_SLIP                (1<<2)
        nmeas = len(self.Svid)
        DelPrMinusAdrM = np.array([np.nan]*nmeas)
        iValid = self.AdrState & (2**0)
        iReset = self.AdrState & (2**1)
        self.AdrM[iValid==0] = np.nan
        for i in range(nmeas):
            DelPrM0 = 0 # to store initial offset from AdrM
            if (not np.isinf(self.AdrM[i])) and (self.AdrM[i] != 0) and (not np.isinf(self.DelPrM[i])) and (iReset[i] == 0):
                # reinitialize after NaNs or AdrM zero or AdrState reset
                if np.isnan(DelPrM0):
                    DelPrM0 = self.DelPrM[i] - self.AdrM[i]
            else:
                DelPrM0 = np.nan
            DelPrMinusAdrM[i] = self.DelPrM[i] - DelPrM0 - self.AdrM[i]
        return DelPrMinusAdrM
            
    def _getPhaseMeas(self):
        return self.ConstComp.processAdrM(self)
    
    def _getDelPr(self):
        return self.ConstComp.getDelPr(self)
    
    def _prepData(self,nmeas,gnssRaw):
        self.ClkDCount = 0
        self.HwDscDelS = 0
        # self.Svid      = 0
        # epoch 1 base-Data
        if self.iepoch == 1:
            self.fullBiasNanos = gnssRaw['FullBiasNanos'][0]
        
        
        self.AzDeg      = np.array([np.nan]*nmeas)
        self.ElDeg      = np.array([np.nan]*nmeas)
        self.tRxSeconds = np.array([np.nan]*nmeas)
        self.tTxSeconds = np.array([np.nan]*nmeas)
        self.PrM        = np.array([np.nan]*nmeas)
        self.PrSigmaM   = np.array([np.nan]*nmeas)
        self.DelPrM     = np.array([np.nan]*nmeas)
        self.PrrMps     = np.array([np.nan]*nmeas)
        self.PrrSigmaMps= np.array([np.nan]*nmeas)
        self.AdrM       = np.array([np.nan]*nmeas)
        self.AdrSigmaM  = np.array([np.nan]*nmeas)
        self.AdrState   = np.zeros(nmeas)
        self.Cn0DbHz    = np.array([np.nan]*nmeas)
        self.ConstellationType  = np.array([np.nan]*nmeas)
        self.CarrierFrequencyHz = np.array([np.nan]*nmeas)
        
        self.freqNum      = np.zeros(nmeas)
        
    def freqSign(self,gnssRaw):
        # gps sys
        gpsfreq = gnssRaw['CarrierFrequencyHz'] * (gnssRaw['ConstellationType'] == 1)
        self.freqNum[np.abs(gpsfreq - GnssConstants.GPS_L1) < 100] = 1
        self.freqNum[np.abs(gpsfreq - GnssConstants.GPS_L5) < 100] = 5
        
        # gls sys
        glsfreq = gnssRaw['CarrierFrequencyHz'] * (gnssRaw['ConstellationType'] == 3)
#        self.freqNum[glsfreq!=0] = 1
        self.freqNum[
                np.abs(np.round((glsfreq - GnssConstants.GLS_L1) / GnssConstants.GLS_dL1) - 
                (gnssRaw['CarrierFrequencyHz'] - GnssConstants.GLS_L1) / GnssConstants.GLS_dL1) < 0.0002
                       ] = 1
        self.freqNum[np.round((glsfreq - GnssConstants.GLS_L1) / GnssConstants.GLS_dL1) > 100] = 0
#        self.freqNum[
#                np.abs(np.round((glsfreq - GnssConstants.GLS_L2) / GnssConstants.GLS_dL2) - 
#                (gnssRaw['CarrierFrequencyHz'] - GnssConstants.GLS_L2) / GnssConstants.GLS_dL2) < 0.0002
#                       ] = 2
        
        # bds sys
        bdsfreq = gnssRaw['CarrierFrequencyHz'] * (gnssRaw['ConstellationType'] == 5)
        self.freqNum[np.abs(bdsfreq - GnssConstants.BDS_B1) < 100] = 1
        self.freqNum[np.abs(bdsfreq - GnssConstants.BDS_B2) < 100] = 2
        
        # gal sys
        galfreq = gnssRaw['CarrierFrequencyHz'] * (gnssRaw['ConstellationType'] == 6)
        self.freqNum[np.abs(galfreq - GnssConstants.GAL_E1) < 100] = 1
        self.freqNum[np.abs(galfreq - GnssConstants.GAL_E5a) < 100] = 5

                
    def process(self,gnssRaw):
        # clean invalid data in gnssRaw
        gnssRaw = self.filterValid(gnssRaw)
        # gnssRaw : dict
        allRxMilliseconds = gnssRaw['allRxMillis'].astype(np.float64)
        self.FctSeconds   = np.unique(allRxMilliseconds) * 1e-3
        self.Svid         = gnssRaw['Svid']
        nmeas = len(self.Svid)
        self._prepData(nmeas,gnssRaw)
        
        # GPS week number
        weekNumber = np.floor( - gnssRaw['FullBiasNanos'] * 1e-9 / GnssConstants.WEEKSEC)
        # GPS day number 
        # dayNumber = np.floor( - gnssRaw['FullBiasNanos']*1e-9 / GnssConstants.DAYSEC)
        # GPS time of week
        towSeconds = (gnssRaw['TimeNanos'] - gnssRaw['BiasNanos']) * 1e-9;
        
        # compute time of measurement relative to start of week
        # subtract big longs (i.e. time from 1980) before casting time of week as double
        weekNumberNanos = np.int64(weekNumber * GnssConstants.WEEKSEC * 1e9)
        
        # compute tRxNanos using gnssRaw.FullBiasNanos(1), so that
        # tRxNanos includes rx clock drift since the first epoch:
        tRxNanos = gnssRaw['TimeNanos'] - self.fullBiasNanos - weekNumberNanos
        gnssRaw['State'] = gnssRaw['State'].astype(np.int)
        State = gnssRaw['State'][0]
#        if not (((State & 2**0) * (State & 2**3)) or ((State & 2**0) * (State & 2**7))) :
        if not ((State & 2**3) or (State & 2**7)) :
            raise Exception('gnssRaw.State[0] must have bits 0 and (3 or 7) before calling Process')
        if not(np.all(tRxNanos >= 0)):
            raise Exception('tRxNanos should be >= 0')
        tRxGnssSeconds = tRxNanos - gnssRaw['TimeOffsetNanos'] - gnssRaw['BiasNanos']
        tRxSeconds = np.zeros(tRxGnssSeconds.shape)
        # tRx at positions of GPS
        gpspos = ((gnssRaw['ConstellationType'] == 1) * (gnssRaw['State'] & 2**3))!=0
        tRxSeconds[gpspos] = np.mod(tRxGnssSeconds[gpspos],GnssConstants.WEEKSEC*1e9)*1e-9
        # tRx at position of BDS
        bdspos = ((gnssRaw['ConstellationType'] == 5) * (gnssRaw['State'] & 2**3))!=0
        tRxSeconds[bdspos] = np.mod(tRxGnssSeconds[bdspos],GnssConstants.WEEKSEC*1e9)*1e-9 - 14
        # tRx at position of GEO
        galpos = ((gnssRaw['ConstellationType'] == 6) * (gnssRaw['State'] & 2**3))!=0
        tRxSeconds[galpos] = np.mod(tRxGnssSeconds[galpos],GnssConstants.MILLISEC*1e9)*1e-9
        # tRx at positions of GLO
        glspos = ((gnssRaw['ConstellationType'] == 3) * (gnssRaw['State'] & 2**7))!=0
        utctime = Time.Gps2Utc(weekNumber,towSeconds,allRxMilliseconds*1e-3)
        leapsecs = Time.LeapSeconds(utctime)
        tRxSeconds[glspos] = np.mod(tRxGnssSeconds[glspos],GnssConstants.DAYSEC*1e9)*1e-9 + (3*60*60 - leapsecs[glspos])
        
        tTxSeconds  = (gnssRaw['ReceivedSvTimeNanos'] + gnssRaw['TimeOffsetNanos'])*1e-9
        prSeconds = tRxSeconds - tTxSeconds
        
        tRxSeconds[glspos==0],prSeconds[glspos==0] = self.checkGpsTimeRollover(tRxSeconds[glspos==0],prSeconds[glspos==0],'week')
        tRxSeconds[glspos],prSeconds[glspos]       = self.checkGpsTimeRollover(tRxSeconds[glspos],prSeconds[glspos],'day')
        
        PrM         = prSeconds * GnssConstants.LIGHTSPEED
        PrSigmaM    = gnssRaw['ReceivedSvTimeUncertaintyNanos'] * 1e-9 * GnssConstants.LIGHTSPEED
        PrrMps      = gnssRaw['PseudorangeRateMetersPerSecond']
        PrrSigmaMps = gnssRaw['PseudorangeRateUncertaintyMetersPerSecond']
        AdrM        = gnssRaw['AccumulatedDeltaRangeMeters']
        AdrSigmaM   = gnssRaw["AccumulatedDeltaRangeUncertaintyMeters"]
        AdrState    = gnssRaw['AccumulatedDeltaRangeState']
        Cn0DbHz     = gnssRaw['Cn0DbHz']
        ConstellationType  = gnssRaw['ConstellationType']
        CarrierFrequencyHz = gnssRaw['CarrierFrequencyHz']
        
        self.fctTime    = weekNumber[0] * GnssConstants.WEEKSEC + tRxSeconds[gpspos][0]
        self.GpsTime    = Time.Fct2Ymdhms(np.array([self.fctTime]))[0]
        self.tRxSeconds = tRxSeconds
        self.tTxSeconds = tTxSeconds
        self.PrM        = PrM
        self.PrSigmaM   = PrSigmaM
        self.PrrMps     = PrrMps
        self.PrrSigmaMps= PrrSigmaMps
        self.AdrM       = AdrM
        self.AdrSigmaM  = AdrSigmaM
        self.AdrState   = AdrState
        self.Cn0DbHz    = Cn0DbHz
        self.ConstellationType = ConstellationType
        self.CarrierFrequencyHz = CarrierFrequencyHz
            
        self.ClkDCount = gnssRaw['HardwareClockDiscontinuityCount'][0]
        
        if gnssRaw['HardwareClockDiscontinuityCount'][0] != gnssRaw['HardwareClockDiscontinuityCount'][-1]:
            raise Exception('HardwareClockDiscontinuityCount changed within the same epoch')
        self.freqSign(gnssRaw)
        self.DelPrM = self._getDelPr()
#        self.PhaseMeas = self._getPhaseMeas()
#        self.PhaseMeas = self.AdrM / AdrMconstBias.getStandardWaveL(self.freqNum,self.ConstellationType,self.CarrierFrequencyHz)
        self.PhaseMeas = self.AdrM / AdrMconstBias.getStandardWaveL(self.freqNum,self.ConstellationType,self.Svid)
        self.PhaseMeas[(self.AdrState & 2**0) == 0] = np.nan
        self.iepoch += 1
        return None
        
    
    
    
    


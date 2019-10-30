# -*- coding: utf-8 -*-
import GnssConstants
import numpy as np
def Gps2Utc(gpsweek,sow,fctSeconds=None):
    if fctSeconds is None:
        fctSeconds = gpsweek * GnssConstants.WEEKSEC + sow
    fct2100 =  6260 * GnssConstants.WEEKSEC + 432000
    if np.any(fctSeconds < 0) or (np.any(fctSeconds >= fct2100)):
        raise Exception('gpsTime must be in this range: [0,0] <= gpsTime(gpsweek,tow) < [6260, 432000]')
    time = Fct2Ymdhms(fctSeconds)    
    
    leapsecs = LeapSeconds(time)
    
    timeMLs = Fct2Ymdhms(fctSeconds-leapsecs)
    
    leapsecsML = LeapSeconds(timeMLs)
    
    if np.all(leapsecsML == leapsecs):
        utcTime = timeMLs
    else:
        utcTime = Fct2Ymdhms(fctSeconds - leapsecsML)
    return utcTime
        
def LeapSeconds(utcTime):
    m,n = utcTime.shape
    if not (n == 6):
        raise Exception('utcTime input must have 6 columns')
    utcTable = [[1982,1,1,0,0,0],
                [1982,7,1,0,0,0],
                [1983,7,1,0,0,0],
                [1985,7,1,0,0,0],
                [1988,1,1,0,0,0],
                [1990,1,1,0,0,0],
                [1991,1,1,0,0,0],
                [1992,7,1,0,0,0],
                [1993,7,1,0,0,0],
                [1994,7,1,0,0,0],
                [1996,1,1,0,0,0],
                [1997,7,1,0,0,0],
                [1999,1,1,0,0,0],
                [2006,1,1,0,0,0],
                [2009,1,1,0,0,0],
                [2012,7,1,0,0,0],
                [2015,7,1,0,0,0],
                [2017,1,1,0,0,0]]
    tableJDays = np.array([md_julday(*iutc[:3]) - GnssConstants.GPSEPOCHJD for iutc in utcTable])
    tableSeconds = tableJDays * GnssConstants.DAYSEC
    jDays = np.array([md_julday(*iutc[:3]) - GnssConstants.GPSEPOCHJD for iutc in utcTime])
    timeSeconds = jDays * GnssConstants.DAYSEC
    leapSecs = np.array([np.sum(tableSeconds <= timeSeconds[i]) for i in range(m)])
    return leapSecs
def Fct2Ymdhms(fctSeconds):
    fctSeconds = np.array(fctSeconds)
    m = fctSeconds.size
    
    HOURSEC = 3600
    MINSEC = 60
    monthDays = [31,28,31,30,31,30,31,31,30,31,30,31]
    
    days = np.floor(fctSeconds / GnssConstants.DAYSEC) + 6 # days since 1980/1/1
    years = np.zeros(m) + 1980
    leap = np.ones(m)
    
    while 1:
        I = days > (leap + 365)
        if np.any(I==False):
            break
        days[I==1] -= (leap[I] + 365)
        years[I==1] += 1
        leap[I==1] = np.fmod(years[I==1],4) == 0
    
    time = np.zeros((m,6))
    time[:,0] = years
    
    for i in range(m):
        month = 1
        if not np.fmod(years[i],4):
            monthDays[1] = 29
        else:
            monthDays[1] = 28
        while days[i] > monthDays[month-1]:
            days[i] -= monthDays[month-1]
            month += 1
        time[i,1] = month
    time[:,2] = days
    sinceMidnightSeconds = np.fmod(fctSeconds,GnssConstants.DAYSEC)
    time[:,3] = np.fix(sinceMidnightSeconds/HOURSEC)
    lastHourSeconds = np.fmod(sinceMidnightSeconds,HOURSEC)
    time[:,4] = np.fix(lastHourSeconds/MINSEC)
    time[:,5] = np.fmod(lastHourSeconds,MINSEC)
    
    return time
            
    
def md_julday(iyear:int,imonth:int,iday:int) -> int:
    "modified julday"
    iyear = int(iyear);imonth = int(imonth);iday = int(iday)
    doy_of_month = [0,31,59,90,120,151,181,212,243,273,304,334]
    if iyear < 0 or imonth < 0 or iday < 0 or imonth > 12 or iday > 366 \
    or (imonth != 0 and iday >31):
        print('***ERROR(modified_julday): incorrect arguments! %s-%s-%s'%(iyear,imonth,iday))
    iyr = iyear
    if imonth <= 2:
        iyr -= 1
    result = 365 * iyear - 678941 + iyr//4 - iyr//100 + iyr//400 +iday
    if imonth != 0:
        result += doy_of_month[imonth-1]
    return result
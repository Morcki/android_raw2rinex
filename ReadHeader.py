# -*- coding: utf-8 -*-
import re
def _checkline(linetext,HeadInfor):
    matchobj = re.search(r'Version:.*?(\w(\d.\d.\d.\d))',linetext)
    if matchobj:
        HeadInfor['Version'] = matchobj.group(1)
    matchobj = re.search(r'Platform:(.*)Manufacturer: ',linetext)
    if matchobj:
        HeadInfor['Platform'] = matchobj.group(1)
    matchobj = re.search(r'Manufacturer:(.*)',linetext)
    if matchobj:
        HeadInfor['Manufacturer'] = matchobj.group(1)
    matchobj = re.search(r'Raw,(.*)',linetext)
    if matchobj:
        HeadInfor['DataFormat'] = matchobj.group(1).split(',')
def _checkHeadInfor(HeadInfor):
    checklist = ['Version','DataFormat']
    for icheck in checklist:
        if not icheck in HeadInfor.keys():
            raise Exception("Invalid GNSS Raw file.")
    if int(HeadInfor['Version'][1]) < 2:
        raise Exception("GNSS logger Version [%s] is lower than 2." % HeadInfor['Version'][1:])
    
    
def read_rawhead(raw_path):
    '''
    Read Header information from gnss rawfile
    Input  :
        raw_path - raw.txt file path [str]
    Output :
        i        - Numbers of HeadLine [int]
        Headinfo - raw file head information [dict]
    '''
    HeadInfor = {}
    with open(raw_path) as f:
        for i,iline in enumerate(f):
            if not (iline[0] == '#'):
                    break
            else:
                _checkline(iline,HeadInfor)
    _checkHeadInfor(HeadInfor)
    return i,HeadInfor
        
    
    
                    
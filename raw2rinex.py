import sys
import json
import getopt
import ReadHeader
from ReadEpoch import RawDataReader
import processGNSSMeas as pro
from convert2rinex import Convert

def raw2rinex(conf_file):
    with open(conf_file) as f:
        conf = json.load(f)
        convertType = conf['type']
        dirpath = conf['dir_path']
        rawpath = conf['raw_path']
    nHead,HeadInfor = ReadHeader.read_rawhead(dirpath + rawpath)
    rawreader = RawDataReader(dirpath + rawpath,nHead,HeadInfor)
    if convertType.upper() == 'RAW':
        rfile = dirpath + rawpath.replace("txt","o")
        # read from rawfile
        gnssRaw = pro.GnssRaw()
        gnssMeas = pro.GnssMeas()
        rinexConv = Convert(rfile,HeadInfor)
        print("START")
        for gnssRaw in rawreader.raw_epochstream(gnssRaw):
            print("Process one raw epoch data...")
            if gnssRaw is None:
                continue
            gnssMeas.process(gnssRaw.gnssRaw)
            if (gnssMeas.iepoch - 1) == 1:
                rinexConv.addRinexHead(gnssMeas)
            rinexConv.gnssmeas2rinex(gnssMeas)
        print('Epoch Number : %d' % (gnssMeas.iepoch - 1))
        print('END')
    elif convertType.upper() == 'FIX':
        rfile = dirpath + rawpath.replace("txt","out")
        gpsLoc = pro.GpsLoc(rfile)
        print("START")
        iepoch = 0
        for lfix in rawreader.fix_epochstream(gpsLoc):
            print("Process one fix epoch data...")
            iepoch += 1
        print('Epoch Number : %d' % iepoch)
        print('END')
    else:
        print("wrong type[%s]! confgure file[type] option: fix/raw." % convertType)
if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hc:",["conf="])
    except getopt.GetoptError:
        print("raw2rinex.py -c <confgure file>")
        sys.exit(2)
    for opt,arg in opts:
        if opt == '-h':
            print("raw2rinex.py -c <confgure file>")
            sys.exit()
        elif opt in ("-c","--conf"):
            conf_file = arg
    raw2rinex(conf_file)
import ReadHeader
from ReadEpoch import RawDataReader
import processGNSSMeas as pro
from convert2rinex import Convert
# obsfile
dir_path = "D:\\PyWorkPlace\\android_raw2rinex\\obsdata\\1017obs\\logger\\MI8\\"
# rawfile name
raw_filepath = "gnss_log_2019_10_17_15_45_43.txt"
#output file path
rfile = dir_path + raw_filepath.replace("txt","o")
# read from rawfile
nHead,HeadInfor = ReadHeader.read_rawhead(dir_path + raw_filepath)
rawreader = RawDataReader(dir_path+raw_filepath,nHead,HeadInfor)
gnssRaw = pro.GnssRaw()
gnssMeas = pro.GnssMeas()
rinexConv = Convert(rfile,HeadInfor)
print("START")
for gnssRaw in rawreader.raw_epochstream(gnssRaw):
    print("Process one epoch data...")
    if gnssRaw is None:
        continue
    gnssMeas.process(gnssRaw.gnssRaw)
    if (gnssMeas.iepoch - 1) == 1:
        rinexConv.addRinexHead(gnssMeas)
    rinexConv.gnssmeas2rinex(gnssMeas)
print('Epoch Number : %d' % (gnssMeas.iepoch - 1))
print('END')






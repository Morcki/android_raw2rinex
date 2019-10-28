# -*- coding: utf-8 -*-
import numpy as np
with open("D:\\PyWorkPlace\\android_raw2rinex\\obsdata\\0929obs\\Logger\\MI8\\gnss_log_onehour.txt",'r') as f:
    
    for i,iline in enumerate(f.readlines()):
        if i == 29:
            v = iline.split(',')
            p = np.int64(v[5])
            print("%18d" % p)
            break
    
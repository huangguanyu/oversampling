#this program is to read mat files.
#by Guanyu Huang

import scipy.io
import numpy as np

def F_matReader(filename):
    data  = scipy.io.loadmat(filename)

    output_subset = {}


    for key_name in data['output_subset'].dtype.names:
        exec(key_name + " =  data['output_subset'][key_name][0][0].flatten()")
        exec('output_subset[key_name]=' + key_name)

    del data

    return output_subset







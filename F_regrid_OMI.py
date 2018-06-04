

# % function to take in the output from F_subset_OMNO2.m or F_subset_OMHCHO.m
# % and regrid these L2 data to a L3 grid, defined by a lat lon box and
# % resolution (Res).

# % the output contains four matrices, A, B, C, and D. A and B are cumulative
# % terms. C = A./B is the regridded concentration over this period. D is the
# % sum of unnormalized spatial response function. Large D means L3 grid is
# % covered by more L2 pixels.

# % written by Kang Sun on 2017/07/14
# revised by Guanyu Huang on 2018/06

from shapely.geometry import Polygon

from oversample_python import F_matReader

import pdb
import os
import matplotlib.pyplot as plt
import scipy.io
import numpy as np
import cv2

def datedev_py(matlab_datenum):
	import datetime

	python_datetime = datetime.datetime.fromordinal(int(matlab_datenum)) + datetime.timedelta(days=matlab_datenum%1) - datetime.timedelta(days = 366)

	return python_datetime

def datenum_py(year, month, day, hour=0, min=0, sec=0):
	import datetime

	if (month<=0) or (month > 12) or (day < 0) or (day > 31):
		return print("Month must be between 1 and 12 and day must be between 1 and 31!")
	else:

		temp_day = datetime.datetime(year, month, day, hour, min, sec)
		

		python_date= (temp_day.toordinal()+ temp_day.hour/24. + temp_day.minute/1440.
			+ temp_day.second/86400. + 366.)
		return python_date


def F_regrid_OMI(inp,output_subset):
	print("start")

	import numpy as np
	#=====================================

	

	Startdate = inp['Startdate']
	Enddate = inp['Enddate']

	Res = inp['res']
	MinLon = inp['MinLon']
	MaxLon = inp['MaxLon']
	MinLat = inp['MinLat']
	MaxLat = inp['MaxLat']

	if 'MarginLon' in inp:
		MarginLon = inp['MarginLon']
	else:
		MarginLon = 0.5

	if 'MarginLat' in inp:
		MarginLat = inp['MarginLat']
	else:
		MarginLat = 0.5

	Startdate = inp['Startdate']
	Enddate = inp['Enddate']

	#max cloud fraction and SZA
	if ('MaxCF' in inp) and ('MaxSZA' in inp):
		MaxCF = inp['MaxCF']
		MaxSZA = inp['MaxSZA']
	else:
		return print("no MaxCF or MaxSZA found.")

	# if xtrack to use
	if 'usextrack' not in inp:
		usextrack = np.arange(60,dtype = int)
	else:
		usextrack = inp['usextrack']

	if ('vcdname' in inp) or ('vcderrorname' in inp):
		vcdname =inp['vcdname']
		vcderrorname = inp['vcderrorname']

	#parameters to define pixel SRF
	if 'inflatex_array' not in inp:
		inflatex_array = np.ones(60)
		inflatey_array = np.ones(60)
	else:
		inflatex_array = inp['inflatex_array']
		inflatey_array = inp['inflatey_array']

	if 'lon_offset_array' not in inp:
		lon_offset_array = np.zeros(60)
		lat_offset_array = np.zeros(60)
	else:
		lon_offset_array = inp['lon_offset_array']
		lat_offset_array = inp['lat_offset_array']

	if 'm_array' not in inp:
		m_array = 4*np.ones(60)
		n_array = 2*np.ones(60)
	else:
		m_array = inp['m_array']
		n_array = inp['m_array']

	# this edition doese not support parallel
	# will do in the next version
	if 'if_parallel' not in inp:
		if_parallel = False
	else:
		if_parallel = inp['if_parallel']


	if 'weekday' in inp:
		useweekday = inp['useweekday']

	 #define x y grids
	xgrid = np.arange(MinLon+0.5*Res,MaxLon, Res)
	ygrid = np.arange(MinLat+0.5*Res,MaxLat, Res)
	nrows = len(ygrid)
	ncols = len(xgrid)

	#define x y mesh
	[Lon_mesh, Lat_mesh] = np.meshgrid(xgrid, ygrid)

	#construct a rectangle envelopes the orginal pixel
	xmargin = 3  #how many times to extend zonally
	ymargin = 2  #how many times to extend meridonally




	f1 = (output_subset['utc'] >= datenum_py(Startdate[0], Startdate[1], Startdate[2], 0, 0, 0)) & \
		(output_subset['utc'] <= datenum_py(Enddate[0], Enddate[1], Enddate[2], 0, 0, 0))

	f2 = (output_subset['latc'] >= MinLat-MarginLat) & (output_subset['latc'] <= MaxLat+MarginLat) & \
		(output_subset['lonc'] >= MinLon-MarginLon) & (output_subset['lonc'] <= MinLon+MarginLon)  & \
		(output_subset['latr'][:,0] >= MinLat-MarginLat*2) & (output_subset['latr'][:,0] <= MaxLat+2*MarginLat) & \
		(output_subset['lonr'][:,0] >= MinLon-MarginLon*2) & (output_subset['lonr'][:,0] <= MaxLon+2*MarginLon)

	f3 = output_subset['sza'] <= MaxSZA

	f4 = output_subset['cloudfrac'] <= MaxCF
	
	f5 = np.in1d(output_subset['ift'], usextrack)

	validmask = f1 & f2 & f4 & f3 & f4 & f5
	

	if 'useweekday' in locals():
		f6 = datetime.datetime(output_subset['utc']).weekday()
		# 0 monday and sunday is 6, return the day of week as an integer

	nL2 = np.sum(validmask)

	if nL2 <= 0:
		return
	else:
		print('Regridding pixels from %s to %s' % (str(Startdate), str(Enddate)))
		print('%d piexels to be regridded...' %nL2) 

	Sum_Above = np.zeros((nrows, ncols))
	Sum_Below = np.zeros((nrows, ncols))
	D = np.zeros((nrows, ncols))

	
	Lat_r = output_subset['latr'][validmask,:]
	Lon_r = output_subset['lonr'][validmask,:]
	Lat_c = output_subset['latc'][validmask]
	Lon_c = output_subset['lonc'][validmask]
	Xtrack= output_subset['ift'][validmask]
	VCD = output_subset[vcdname][validmask]
	VCDe = output_subset[vcderrorname][validmask]


	if if_parallel:
		print('prallel computation will be supported in our next version!')
	else:
		count = 1
		for iL2 in range(nL2-1):


			lat_r = Lat_r[iL2,:]
			lon_r = Lon_r[iL2,:]
			lat_c = Lat_c[iL2]
			lon_c = Lon_c[iL2]
			vcd = VCD[iL2]
			vcd_unc = VCDe[iL2]
			xtrack = int(Xtrack[iL2])


			inflatex = inflatex_array[xtrack]
			inflatey = inflatey_array[xtrack]
			lon_offset = lon_offset_array[xtrack]
			lat_offset = lat_offset_array[xtrack]
			m = m_array[xtrack]
			n = n_array[xtrack]
			

			tp_poly = np.column_stack((lon_r[:], lat_r[:]))
			
			A = Polygon(tp_poly).area
			
			

			lat_min = lat_r.min()
			lon_min = lon_r.min()
			
			local_left = lon_c- xmargin*(lon_c - lon_min)
			local_right = lon_c+xmargin*(lon_c - lon_min)

			local_bottom = lat_c- ymargin*(lat_c - lat_min)
			local_top = lat_c + ymargin*(lat_c - lat_min)

			lon_index = (xgrid >= local_left) & (xgrid <= local_right)
			lat_index = (ygrid >= local_bottom) & (ygrid <= local_top)

			
			
			if (lat_index.any() and lon_index.any()) == True:
				
				print(str(count), str(iL2))

				lon_mesh = Lon_mesh[lat_index, :][:, lon_index]
				lat_mesh = Lat_mesh[lat_index, :][:, lon_index]

				SG = F_2D_SG_transform(lon_mesh, lat_mesh, lon_r, lat_r, lon_c, lat_c, m,n, inflatex, inflatey, lon_offset, lat_offset)
				
				
				sum_above_local = np.zeros((nrows,ncols))
				sum_below_local = np.zeros((nrows,ncols))
				D_local = np.zeros((nrows, ncols))
				
				local_id =np.ix_(lat_index,lon_index)
				D_local[local_id] = SG

				sum_above_local[local_id] = SG/A/vcd_unc*vcd
				sum_below_local[local_id] = SG/A/vcd_unc
				Sum_Above = Sum_Above + sum_above_local
				Sum_Below =	 Sum_Below + sum_below_local
				D = D+D_local
				
			


			if iL2 == (count*np.round(nL2/10)):
				print('%s finished' % str(count*10))
				count = count +1

	print("completed function")
	output_regrid = {'A': Sum_Above, 'B': Sum_Below, 'C': Sum_Above/Sum_Below, 'D': D,
		'xgrid': xgrid, 'ygrid': ygrid}

	return output_regrid



def F_2D_SG_transform(xmesh,ymesh,x_r,y_r,x_c,y_c,m=4,n=2,inflatex=1,inflatey=1,x_offset=0,y_offset=0):
    
    vList = np.column_stack((x_r-x_c,y_r-y_c))
    leftpoint = np.mean(vList[0:2,:],axis=0)
    rightpoint = np.mean(vList[2:4,:],axis=0)
    uppoint = np.mean(vList[1:3,:],axis=0)
    lowpoint = np.mean(vList[[0,3],:],axis=0)
    xvector = rightpoint-leftpoint
    yvector = uppoint-lowpoint

    FWHMx = np.linalg.norm(xvector)
    FWHMy = np.linalg.norm(yvector)

    fixedPoints = np.float32([[-FWHMx,-FWHMy],[-FWHMx,FWHMy],[FWHMx,FWHMy],[FWHMx,-FWHMy]])/2
    tform = cv2.getPerspectiveTransform(vList,fixedPoints)
    
    xym1 = np.column_stack((xmesh.flatten()-x_c-x_offset,ymesh.flatten()-y_c-y_offset))
    xym2 = np.hstack((xym1,np.ones((xmesh.size,1)))).dot(tform.T)[:,0:2]
    FWHMy = FWHMy*inflatey
    FWHMx = FWHMx*inflatex

    wx = FWHMx/2/(np.log(2))**(1/m)
    wy = FWHMy/2/(np.log(2))**(1/n)

    SG0 = np.exp(-(np.abs(xym2[:,0])/wx)**m-(np.abs(xym2[:,1])/wy)**n)
    meshsize = np.shape(xmesh)


    if xmesh.ndim == 1:
        SG = SG0
    else:
        SG = np.reshape(SG0,(meshsize[0],meshsize[1]))

    return SG


#===========================================================
# test
#==========================================================

fn = 'C:/Users/ghuang/Documents/GitHub/oversampling/sample_data_OMNO2.mat'
output_subset = F_matReader(fn)


inp = {}
inp['Startdate'] = (2005, 7,2)
inp['Enddate'] = (2005,7, 5)

inp['res'] = 0.1
inp['MinLon'] = -105 
inp['MaxLon'] = -101
inp['MinLat'] = 38
inp['MaxLat'] = 40
inp['MaxCF'] = 0.3
inp['MaxSZA'] = 75
inp['vcdname'] = 'colno2' 
inp['vcderrorname'] = 'colno2error'

test=F_regrid_OMI(inp, output_subset)

pdb.set_trace()

# Function to transfer lat lon to x y in km using Lambert standard
# projection. Need to define center lat lon.

# Written by Kang Sun on 2017/09/23

# major bug-fix on 2017/11/20 to use mercator projection near equator
# instead of lambert

# migrated to python version by Guanyu Huang 4/25/2018


import datetime


def F_latlon2xy(inp):

	import pyproj
	import math

	clon = inp['clon']
	clat = inp['clat']

	if clon < 0:
		clon = 360+clon

	pdb.set_trace()

	if abs(clat) < 15:
		outproj = pyproj.Proj('+proj=merc +ellps=WGS84 +datum=WGS84 +no_defs')

	else:
		outproj = pyproj.Proj('+proj=lcc +lon_0=-90 +datum=WGS84 +no_defs +lat_1 =%d +lat_0=%d'/ )

	pdb.set_trace()

	#inpproj = pyproj.Proj("+proj=stere +lat_0=90 +lat_ts=60 +lon_0=-105 +k=90 +x_0=0 +y_0=0 +a=6371200 +b=6371200 +units=m +no_defs")
	

	#outproj = pyproj.Proj(projtype)

	inpproj = pyproj.Proj('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

	x,y = pyproj.transform(inpproj, outproj, clon,clat)

	return x,y

# #test

# inp ={'clon': 90, 'clat': 45}

# print(F_latlon2xy(inp))

def F_oversample_OMI_km(inp, ouput_subset):

 	output_oversample = {}

 	A_array = [4596.47998046875,3296.36010742188,
 		2531.02001953125,2022.28002929688,1664.44995117188,
 		1402.01000976563,1202.15002441406,1046.56994628906,
 		922.939025878906,823.557983398438,742.541015625000,
 		676.026977539063,620.728027343750,574.632019042969,
 		535.745971679688,502.919006347656,474.923004150391,
 		451.101989746094,430.649993896484,413.221008300781,
 		398.187011718750,385.433013916016,374.503997802734,
 		365.376007080078,357.684997558594,351.493011474609,
 		346.483001708984,342.816009521484,340.184997558594,
 		338.792999267578,338.364990234375,339.161010742188,
 		340.954010009766,344.029998779297,348.161010742188,
 		353.752990722656,360.536010742188,369.022003173828,
 		378.957000732422,390.996002197266,404.904998779297,
 		421.479003906250,440.553985595703,463.213012695313,
 		489.364013671875,520.383972167969,556.742004394531,
 		599.838012695313,651.012023925781,712.447998046875,
 		786.658996582031,877.330993652344,989.809020996094,
 		1131.55004882813,1313.92004394531,1554.43994140625,
 		1881.34997558594,2340.41992187500,3012.80004882813,4130.99023437500]

 	Startdate = inp['Startdate']
	Enddate = inp['Enddate']

	res = inp['res']
	max_x = inp['max_x']
	max_y = inp['max_y']
	clon = inp['clo']
	clat = inp['clat']
	R = inp['R']

	if 'do_weight' not inp:
		do_weight = False
	else:
		do_weight = inp['do_weight']

	max_lon = clon+max_x*1.2/110/math.cos((abs(clat)+max_y/111)/180*math.pi)
	min_lon = clon-max_x*1.2/110/math.cos((abs(clat)+max_y/111)/180*math.pi)
	max_lat = clat+max_y*1.2/110
	min_lat = clat-max_y*1.2/110

#define x y grids
	xgrid = np.arrange(-1*max_x+0.5*res, max_x, res)
	ygrid = np.arrange(-1*max_y+0.5*res, max_y, res)
	nrows = len(ygrid)
	ncols = len(xgrid)

#define x y mesh
	xmesh, ymesh = np.meshgrid(xgrid, ygrid)

#define 
	MaxCF = inp['MaxCF']
	MaxSZA = inp['MaxSZA']

# xtrack to use

	if 'usextrack' not in inp:
		usextrack =1:60
	else:
		usextrack = inp['usextrack']

	vcdname = inp['vcdname']
	vcderrorname = inp['vcderrorname']

	if 'useweekday' in inp:
		useweekday = inp['useweekday']

	if 'if_parallel' in inp:
		if_parallel = False

	else
		if_parallel = inp.if_parallel


f1 = output_subset['utc']+366 >= datetime.datetime(Startdate, 0, 0, 0).toordinal() &
	output_subset['utc']+366 <= datetime.datetime(Enddate 23 59 59).toordinal()

f2 = output_subset['latc'] >= min_lat-0.5 & output_subset['latc'] <= max_lat +0.5 &
	output_subset['lonc'] >= min_lon-0.5 & output_subset['lonc'] <= max_lon +0.5 &
	output_subset['latr'][:,1] >= min_lat-1 & output_subset['latr'][:,1] <= max_lat+1 &
	output_subset['lonr'][:,1] >= min_lon-1 & output_subset['lonr'][:,1] <= max_lon+1

f3 = output_subset['sza'] <= MaxSZA

f4 = output_subset['cloudfrac'] <= MaxCF

f5 = np.in1d(output_subset['ift'], usextrack)

validmask = f1 & f2 & f3 & f4 & f5

if 'useweekday' in locals():
	f6 = datetime.datetime(output_subset['utc']).weekday()
	# 0 monday and sunday is 6, return the day of week as an integer

nL2 = np.sum(validmask)

if nL2 <= 0:
	return
else:
	print('Regridding pixels from %d to %d' (Startdate, Enddate))
	print('%d piexels to be regridded...')

Lat_c = output_subset['latc'][validmask]


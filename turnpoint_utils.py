#!/usr/bin/pythin

"""
handle turnpoint data files, analyze, look for duplicates etc
Niv Levy June 2015 GPL v2
"""

import pandas as pd
from numpy import isnan, nan, sin, cos, arctan , pi
import numpy as np
from geopy.distance import GreatCircleDistance
from geopy.point import Point
from itertools import combinations
import tempfile, os, copy

#test files:
# '/home/niv/Downloads/crystal15.dat.dat'
# '/home/niv/Downloads/avenal12.dat'

crystal_airport = Point('34.484885, -117.826479, 3420 ft')

class dat (object):
    """
    class for storing turnpoint details. The parsed data will be stored as a list where each membr is of he structure of x = { 'point' : (geopy point), 'type' : (landable, turnpoint...), 'name' : ..., 'comment' : ' '}
    """
    
    def __init__(self, filename):
	# TODO : modify so that we can easily add a file!
	self.filename = filename
	if type(filename) == str:
	    self.parse_dat_file(filename)
	elif type(filename) == list:
	    #use the shell to concatanate the files; obviously not os agnostic
	    t = tempfile.NamedTemporaryFile()
	    print 'cat ' + ' '.join(filename) + ' > ' + t.name
	    os.system('cat ' + ' '.join(filename) + ' > ' + t.name)
	    self.parse_dat_file(t.name)
	    t.close()
	self.list_turnpoints()
    
    def parse_dat_file(self, filename):
	"""
	parse a turnpoint file in dat format
	"""
	self.data = pd.read_csv(filename, sep = ',', names = ['index', 'Lat', 'Long', 'alt', 'type', 'name', 'comment'], comment = '*').dropna(how='all')
	#it's not handling comments properly, which is why trying to dtype it failed, and why the dropna was required.
	return

    def make_latlong_s(self, data_series):
	"""
	convert a list of strings in a few possible format to a lat / long string that gropy can stomach
	meant for hundreds of points at most, so does not need to be super fast
	"""
	#print '**', data_series, '**'
	return_s =[''] * len(data_series)
	for i, s in enumerate(data_series):
	    try:
		t = s.strip().split(':')
		if len(t) == 1:
		    return_s[i] = s + ' '
		elif len(t) == 2: # degres and decimal minutes
		    return_s[i] =  str(float(t[0]) + float(t[1][:-1]) / 60.0) + t[1][-1] + ' ' 
		elif len(t) == 3: # deg, min, sec
		    return_s[i] =  str(float(t[0]) + float(t[1]) / 60.0 + float(t[2][:-1]) / 3600.0) + t[2][-1] + ' '
	    except AttributeError:
		return_s[i] = nan
	return np.array(return_s)

    def list_turnpoints(self):
	"""
	add a geopy encoded point
	"""
	self.data['Long_s'] = self.make_latlong_s(self.data['Long'])
	self.data['Lat_s'] = self.make_latlong_s(self.data['Lat'])
	d = [''] * len(self.data['alt'])
	for i, s in enumerate(self.data['alt']):
	    try:
		d[i] = str(float(s.strip('F')) * 0.304) + ' m' # seems not to like ft?!
	    except AttributeError:
		d[i] = nan
	self.data['Alt_s'] = np.array(d)
	self.data['point_s'] = self.data['Lat_s'] + self.data['Long_s'] + self.data['Alt_s']
	#print data
	self.turn_points = [{'point' : Point(), 'type' : '', 'name' : '', 'comment' : ''}] * len(self.data)
	for i,s in enumerate(self.data['point_s']):
	    try:
		if type(self.data['comment'].iloc[i]) != str:
		    self.turn_points[i] = {'point' : Point(s), 'type' : self.data['type'].iloc[i], 'name' : self.data['name'].iloc[i], 'comment' : ''}
		else:
		    self.turn_points[i] = {'point' : Point(s), 'type' : self.data['type'].iloc[i], 'name' : self.data['name'].iloc[i], 'comment' : self.data['comment'].iloc[i]}
	    except ValueError:
		print 'Failed to parse ', self.data.iloc[i]
	# seems pandas cant handle this data type nicely
	#data['point'] = points
	return

def format_angle(a, lat_lon):
    """
    format angle into deg:min with min having three decimal points
    """
    if lat_lon == 'lat':
	if a < 0:
	    D = 'S'
	else:
	    D = 'N'
    elif lat_lon == 'lon':
	if a < 0 :
	    D = 'W'
	else:
	    D = 'E'
    else:
	print 'wrong choice'
	return None
    return '{:0d}:{:0.3f}'.format(int(a), 60.0 * abs(a - int(a))) + D

#457,33:39.736N,113:45.979W,1175F,L,Vicksburg,15x1500 n/sD levee pwrl Nend emergency
def tp2dat(filename, turn_points):
    """
    write a list of turn points back to a dat file
    #TODO : check if this is legit, if locations are correct etc
    """
    #TODO : check existnece
    f = open(filename, 'w')
    for i, tp in enumerate(turn_points):
	lat = tp['point'].latitude
	lon = tp['point'].longitude
	alt = '{:0d}F'.format(int(tp['point'].altitude / 0.304 * 1000.0))
	try:
	    f.write(','.join([str(i), format_angle(lat, 'lat'), format_angle(lon, 'lon'), alt, tp['type'], tp['name'], tp['comment']]) + '\n')
	except TypeError:
	    print 'failed to print ', tp, ' to file'
    f.close()

def rad2deg(a):
    return float(a) * 180.0/pi

def deg2rad(a):
    return float(a) * pi / 180.0

# from http://stackoverflow.com/questions/17624310/geopy-calculating-gps-heading-bearing
def p2p_bearing(pt1, pt2):
    """
    take two points (in geopy represntation) and return a bearing in the range of 0-360 deg
    """
    lat1 = deg2rad(pt1.latitude)
    lat2 = deg2rad(pt2.latitude)
    lon1 = deg2rad(pt1.longitude)
    lon2 = deg2rad(pt2.longitude)
    dLon = lon2 - lon1;
    y = sin(dLon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
    return (rad2deg(arctan(y / x))) % 360
    
	
def tp_in_sector(origin, turn_points, direction, width, verbose = True):
    """
    return all tp that are in a sector from a given point
    origin - a geopy point
    turn_points - list in the format of the tp list stored in the dat class
    sort based on distanc to origin
    """
    #for tp in turn_points:
	#print tp['comment'], ' ', abs(p2p_bearing(origin, tp['point']) - direction)
    sector_pts = [tp for tp in turn_points if abs(p2p_bearing(origin, tp['point']) - direction) < float(width) /2]
    sector_pts.sort(key = lambda x : GreatCircleDistance(origin, x['point']))
    
    if verbose:
	for tp in sector_pts:      
	    print tp['name'], 'bearing = ', p2p_bearing(origin, tp['point']), 'R = ', GreatCircleDistance(origin, tp['point'])
    return sector_pts


def check_for_duplicates(files, min_distance = 1.0):
    """
    take one or more files, and return two list of turnpoints- one that is the combination of all unique points in both, and one that contains points which are likely duplicates, based on relative distances
    """
    data = dat(files)
    unique = copy.deepcopy(data.turn_points)
    duplicates = []
    for i, j in combinations(data.turn_points, 2):
	print 'Testing ', i['name'], j['name']
	if GreatCircleDistance(i['point'], j['point']) < min_distance:
	    duplicates.append(i)
	    duplicates.append(j)
    for tp in duplicates:
	try:
	    unique.remove(tp)
	except ValueError: # more than two points can share the same space!
	    print 'Could not remove ', tp
    return unique, duplicates
    
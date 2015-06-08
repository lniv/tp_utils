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

#test files:
# '/home/niv/Downloads/crystal15.dat.dat'
# '/home/niv/Downloads/avenal12.dat'

crystal_airport = Point('34.484885, -117.826479, 3420 ft')

class dat (object):
    """
    class for storing turnpoint details. The parsed data will be stored as a list where each membr is of he structure of x = { 'point' : (geopy point), 'type' : (landable, turnpoint...), 'comment' : ' '}
    """
    
    def __init__(self, filename):
	self.filename = filename
	self.parse_dat_file()
	self.list_turnpoints()
    
    def parse_dat_file(self):
	"""
	parse a turnpoint file in dat format
	"""
	self.data = pd.read_csv(self.filename, sep = ',', names = ['index', 'Lat', 'Long', 'alt', 'type', 'comment'], comment = '*').dropna(how='all')
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
		d[i] = s.strip('F') + ' ft'
	    except AttributeError:
		d[i] = nan
	self.data['Alt_s'] = np.array(d)
	self.data['point_s'] = self.data['Lat_s'] + self.data['Long_s'] + self.data['Alt_s']
	#print data
	self.turn_points = [{'point' : Point(), 'type' : '', 'comment' : ''}] * len(self.data)
	for i,s in enumerate(self.data['point_s']):
	    try:
		self.turn_points[i] = {'point' : Point(s), 'type' : self.data['type'].iloc[i], 'comment' : self.data['comment'].iloc[i]}
	    except ValueError:
		print 'Failed to parse ', self.data.iloc[i]
	# seems pandas cant handle this data type nicely
	#data['point'] = points
	return


def rad2deg(a):
    return float(a) * 180.0/pi

def deg2rad(a):
    return float(a) * pi / 180.0

# from http://stackoverflow.com/questions/17624310/geopy-calculating-gps-heading-bearing

def p2p_bearing(pt1, pt2):
    """
    take two points (in geopy represntation and return a bearing in the range of 0-360 deg
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
	    print tp['comment'], 'bearing = ', p2p_bearing(origin, tp['point']), 'R = ', GreatCircleDistance(origin, tp['point'])
    return sector_pts
    
    


def check_for_duplicates(file1, file2, min_distance):
    """
    take two data objects, and return two - one that is the combination of all unique points in both, and one that contains points which are likely duplicates
    """
    data1 = dat(file1)
    data2 = dat(file2)
    marge(data1,data2)
    
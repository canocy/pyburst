from unittest import TestCase

import math
import numpy
from numpy.random import uniform

import lal
from gwpy.timeseries import TimeSeries

import pyburst as pb
import pyburst.detectors, pyburst.skymaps

TIME = lal.LIGOTimeGPS(630720013) # Jan 1 2000, 00:00 UTC
SAMPLING_RATE = 4096.0 # Hz
T = numpy.arange(int(SAMPLING_RATE))/SAMPLING_RATE

F0 = 200 # Hz
SINE_1_SEC = numpy.sin(2*math.pi*F0*T)
ZEROS_1_SEC = numpy.zeros(int(SAMPLING_RATE))
ZEROS_5_SEC = numpy.zeros(int(5 * SAMPLING_RATE))

class TestDetector(TestCase):

    def test_antenna_pattern(self):
        """ Check consistency of antenna pattern computed using two coordinate systems
        """
        coords = numpy.array([uniform(0,360), uniform(-90,90)])
        pt_eq = pb.skymaps.Skypoint(*numpy.radians(coords), 'equatorial')
        pt_geo = pt_eq.transformed_to('geographic', TIME)
        d = pb.detectors.Detector('V1')
        pat_eq = d.antenna_pattern(pt_eq, ref_time=TIME)
        pat_geo = d.antenna_pattern(pt_geo, ref_time=None)

        self.assertAlmostEqual(pat_eq[0], pat_geo[0]) # fplus
        self.assertAlmostEqual(pat_eq[1], pat_geo[1]) # fcross

    def test_delay(self):
        """ Check consistency of delay computed using two coordinate systems
        """
        coords = numpy.array([uniform(0,360), uniform(-90,90)])
        pt_eq = pb.skymaps.Skypoint(*numpy.radians(coords), 'equatorial')
        pt_geo = pt_eq.transformed_to('geographic', TIME)
        d = pb.detectors.Detector('V1')
        dt_eq = d.time_delay_from_earth_center(pt_eq, ref_time=TIME)
        dt_geo = d.time_delay_from_earth_center(pt_geo)

        self.assertAlmostEqual(dt_eq, dt_geo, places=5)
    
    def test_delay_project_strain(self):
        """ Check consistency of project_strain() with time_delay_earth_center()
        """

        coords = numpy.array([uniform(0,360), uniform(-90,90)])
        
        pt_eq = pb.skymaps.Skypoint(*numpy.radians(coords), 'equatorial')
        d = pb.detectors.Detector('V1')
        delay = d.time_delay_from_earth_center(pt_eq, TIME)
    
        hplus = TimeSeries(ZEROS_1_SEC, sample_rate=SAMPLING_RATE).to_lal()
        hcross = TimeSeries(SINE_1_SEC, sample_rate=SAMPLING_RATE).to_lal()
        hplus.epoch = lal.LIGOTimeGPS(TIME)
        hcross.epoch = lal.LIGOTimeGPS(TIME)

        # Project wave onto detector
        response = d.project_strain(hplus, hcross, TIME, \
                                    *pt_eq.coords(fmt='lonlat', unit='radians'), 0)
                
        # Generate support timeseries
        data = TimeSeries(ZEROS_5_SEC, \
                          sample_rate=SAMPLING_RATE, \
                          t0=TIME-2, unit=response._unit)

        # Inject signal into timeseries
        h = data.inject(response)
        
        # Find end of the detector response
        ix, = numpy.where(numpy.abs(h) > numpy.max(h)/10)
        time_end = h.t0.value + ix[-1]/SAMPLING_RATE
        estimated_delay = float(time_end - (TIME+1))
        
        print("Exact delay = {} ; Estimated delay = {}".format(delay, estimated_delay))
        
        # Estimate delay from timeseries
        self.assertAlmostEqual(delay, estimated_delay, places=3)

    def test_amplitude_project_strain(self):
        """ Check consistency of project_strain() with antenna_pattern()
        """

        coords = numpy.array([uniform(0,360), uniform(-90,90)])
        psi = math.radians(uniform(0,180))
        
        pt_eq = pb.skymaps.Skypoint(*numpy.radians(coords), 'equatorial')
        d = pb.detectors.Detector('V1')
        antenna_pat = d.antenna_pattern(pt_eq, ref_time=TIME, psi=psi)
        
        hplus = TimeSeries(ZEROS_1_SEC, sample_rate=SAMPLING_RATE).to_lal()
        hcross = TimeSeries(SINE_1_SEC, sample_rate=SAMPLING_RATE).to_lal()
        hplus.epoch = lal.LIGOTimeGPS(TIME)
        hcross.epoch = lal.LIGOTimeGPS(TIME)
            
        # Project wave onto detector
        response = d.project_strain(hplus, hcross, TIME, \
                                    *pt_eq.coords(fmt='lonlat', unit='radians'), psi)
                
        # Generate support timeseries
        data = TimeSeries(ZEROS_5_SEC, \
                          sample_rate=SAMPLING_RATE, \
                          t0=TIME-2, unit=response._unit)

        # Inject signal into timeseries
        h = data.inject(response)
        estimated_pat = h.max().to_value()

        print("Exact antenna pattern = {} ; Estimated amplitude = {}".format(antenna_pat[0], estimated_pat))
            
        # Estimate delay from timeseries
        self.assertAlmostEqual(antenna_pat[0], estimated_pat, places=5)
            
# Test sky points in grid have similar antennna patterns and delays

# close_pixels = healpy.pixelfunc.get_interp_weights(sky.nside,*pt_geo.coords(fmt='colatlon'),sky.order)
# for ix in close_pixels[0]:
#    print('ix={}: patterns: {}, delays: {}'.format(ix,antenna_patterns[ix],delays[ix]))

# lon, lat = sky.grid.healpix_to_lonlat(range(sky.grid.npix))

# fig, axes = plt.subplots()
# for lo,la in zip(lon,lat):
#    plt.plot(lo, la,'g.')
# plt.plot(pt_geo.lon, pt_geo.lat,'rx')
# for ix in close_pixels[0]:
#     print(ix)
#     plt.plot(lon[ix], lat[ix],'b.')

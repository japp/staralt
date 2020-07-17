"""
Additional astropy Locations not included in
coordinates.EarthLocation.get_site_names()

"""

from astropy.coordinates import SkyCoord
from astroplan import FixedTarget, Observer
from astropy import units as u
from astropy.coordinates import EarthLocation
from pytz import timezone


def OT_observer():
    """
    OT Location
    """

    longitude = '-16d30m35s'
    latitude = '+28d18m00s'
    elevation = 2390 * u.m
    location = EarthLocation.from_geodetic(longitude, latitude, elevation)

    observer = Observer(name='Observatorio del Teide',
                        location=location,
                        timezone=timezone('Atlantic/Canary'),
                        description="Observatorio del Teide, Tenerife, Spain")

    return observer


def CAHA_observer():
    """
    CAHA Location
    """

    longitude = '-2d32m46s'
    latitude = '+37d13m25s'
    elevation =  2168*u.m
    location = EarthLocation.from_geodetic(longitude, latitude, elevation)

    observer = Observer(name='Observatorio de Calar Alto',
                        location=location,
                        timezone=timezone('Europe/Madrid'),
                        description="Observatorio de Calar Alto, Almeria, Spain")

    return observer


def OAO_observer():
    """
    Okayama Astrophysical Observatory Location
    """

    from astropy.coordinates import EarthLocation
    from pytz import timezone

    longitude = '133d35m38s'
    latitude = '+34d34m28s'
    elevation =  370*u.m
    location = EarthLocation.from_geodetic(longitude, latitude, elevation)

    observer = Observer(name='Okayama Astrophysical Observatory (OAO)',
                        location=location,
                        timezone=timezone('JST'), # Japan Standard Time
                        description="Okayama Astrophysical Observatory (NAOJ), Japan")

    return observer

# -*- coding: utf-8 -*-
"""
General library for altitude plots and observability

"""

import numpy as np
import datetime
import pytz
from astropy.time import Time
import matplotlib.dates as mdates
from astropy import units as u
from app.locations import *

import matplotlib
from matplotlib.figure import Figure
import matplotlib.dates as dates
from matplotlib.pyplot import style

style.use('fast')


def staralt(observatory, observation_date, objects, transits=[], twilight='astronomical'):
    """
    Plot altitude curves for a list of objects

    Parameters
    ----------
    observatory : str
        Observatory code
    observation_date : datetime.datetime
        Date of observation
    objects : list (optional)
        List of dict of object to plot
    transits : list (optional)
        List of dict of transits to plot
    twilight : str (optional)
        Twilight limits to plot: civil, nautical or astronomical

    Returns
    -------
    image : image/png
        Altitude plot in PNG format

    """

    # Site location
    location = get_location(observatory)

    # Observation date string to use the graph
    obs_date = observation_date.strftime("%-d of %B, %Y")

    # Observation date in Time object
    observation_date_Time = Time(observation_date.strftime("%Y-%m-%d 12:00"))

    # Position of twilights, sun rising and setting
    # Sun's rising and setting time, in astropy.Time object
    setting_time = location.sun_set_time(observation_date_Time).datetime
    rising_time = location.sun_rise_time(observation_date_Time, which='next').datetime
    
    # twilights in astropy.Time object
    if twilight == 'civil':
        twilight1 = location.twilight_evening_civil(observation_date_Time).datetime
        twilight2 = location.twilight_morning_civil(observation_date_Time, which='next').datetime
    if twilight == 'nautical':
        twilight1 = location.twilight_evening_nautical(observation_date_Time).datetime
        twilight2 = location.twilight_morning_nautical(observation_date_Time, which='next').datetime
    else:
        twilight1 = location.twilight_evening_astronomical(observation_date_Time).datetime
        twilight2 = location.twilight_morning_astronomical(observation_date_Time, which='next').datetime

    # -- Plotting -------------------------------

    fig = Figure(figsize=(11, 6))
    fig.set_facecolor("white")

    ax = fig.add_subplot(111)
    fig.subplots_adjust(top=0.93, right=0.88, wspace=0.01, bottom=0.24)
    

    # --- Objects altitude curves -------------
    visible_time = Time(setting_time + (rising_time - setting_time)*np.linspace(0, 1, 100))

    # dict to store the line color of the plots, to use
    # in transits if required
    object_colors = {}
    for obj in objects:

        coordinates = SkyCoord(obj['RA'], obj['Dec'], unit='deg')
        target = FixedTarget(name=obj['name'], coord=coordinates)

        altaz = location.altaz(visible_time, target)

        object_label = '{:s}'.format(obj['name'])
        object_curve, = ax.plot(visible_time.datetime, altaz.alt.deg, label=object_label)
        object_colors[obj['name']] = object_curve.get_color()

    # Moon altitude curve
    ax.plot(visible_time.datetime, location.moon_altaz(visible_time).alt,
            lw=10, alpha=0.2, color='k', label='Moon')

    # midnight, because the computation day (observation day + 1 day)
    ax.axvline(observation_date + datetime.timedelta(days=1), c='k')
    ax.grid()

    # Twilight band limits
    # Are the sun setting and rising times, which
    # are the first and last elements in fractions_days list
    ax.axvspan(setting_time, twilight1, color='k', alpha=0.1)
    ax.axvspan(twilight2, rising_time, color='k', alpha=0.1)

    ylabels = []
    yticks_values = np.arange(0, 91, 10)

    for ang in yticks_values:
        ylabels.append(str(ang) + "$^\circ$")

    ylabels[0] = ""

    # setting time in date (without time)
    setting_time_date = datetime.datetime.combine(setting_time.date(), datetime.datetime.min.time())

    # Observable hour during the night (int)
    obs_hours = int((rising_time - setting_time).total_seconds()/3600)

    # list of datetimes for X axis labels
    xticks_utc = []
    xticks_local = []
    xlabels = []

    for h in range(0, obs_hours+1):
        # Set hour in UTC, just in case
        h_utc = setting_time_date.replace(tzinfo=pytz.utc) + datetime.timedelta(hours=setting_time.hour + h)
        xticks_utc.append(h_utc)


        h_local = h_utc.astimezone(tz=location.timezone)
        
        xticks_local.append(h_local)

        xlabels.append("{utc:.0f}\n{local:.0f}".format(utc=int(h_utc.strftime("%H")), local=int(h_local.strftime("%H"))))

    ax.set_xticks(xticks_utc)
    ax.set_xticklabels(xlabels)

    # x axis date format in hours.
    # Add a hyphen between the % and the letter to remove the leading zero (01 -> 1).
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%-H'))

    # --- Y axis ----
    # set the values and labels of the yticks
    ax.set_yticklabels(ylabels)
    ax_airmass = ax.twinx()

    # set the values and labels of the yticks
    ax_airmass_labels = np.round(1/np.cos(np.radians(90-yticks_values)), 2)
    ax_airmass.set_yticks(yticks_values)
    ax_airmass_labels = ax_airmass_labels.tolist()
    ax_airmass_labels[0] = ""
    ax_airmass.set_yticklabels(ax_airmass_labels)
    ax_airmass.set_ylabel("Airmass")

    # Plotting limits are sun setting and rising, which
    # are the first and last elements in fractions_days list
    ax.set_xlim(setting_time, rising_time)
    ax.set_xlabel('UT (up) and Local Time, starting night {}'.format(obs_date))

    # Upper x axis with sidereal time
    # -------------------------------
    # sidereal time upper ticks are cloned from xticks (UT local time) using
    # ax.get_xticks(), which returns a list of floats  which gives the number
    # of days (fraction part represents hours, minutes, seconds) since
    # 0001-01-01 00:00:00 UTC *plus* *one* (historical reasons)
    # Then this float must be converted to datetime with num2date and then
    # to astropy.Time to compute the sidereal time for each value, properly formatted
    ax_sidereal_time = ax.twiny()
    ax_sidereal_time_ticks = ax.get_xticks()
    ax_sidereal_time.set_xticks(ax_sidereal_time_ticks)
    ax_sidereal_time.set_xbound(ax.get_xbound())

    sidereal_times = []
    dates_datetime = Time(dates.num2date(ax.get_xticks()))

    for sidereal in dates_datetime.sidereal_time(
            kind='mean', longitude=location.location.lon):
        sidereal_times.append("{:02.0f}:{:02.0f}".format(sidereal.hms.h, sidereal.hms.m))

    ax_sidereal_time.set_xticklabels(sidereal_times)
    ax_sidereal_time.set_xlabel('Local sidereal time at {}'.format(observatory), fontsize=10)

    # Transit band limits, if any.
    # Dates in YYYY-MM-SS hh:mm format. seconds are removed if included
    if transits:
        for transit in transits:
            t_early = datetime.datetime.strptime(transit['t_early'][:16], "%Y-%m-%d %H:%M")
            t_late = datetime.datetime.strptime(transit['t_late'][:16], "%Y-%m-%d %H:%M")

            ax.axvspan(t_early, t_late, color=object_colors[transit['name']], alpha=0.2)

    ax.set_ylim(0, 90)
    ax.set_ylabel('Altitude')

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=False, shadow=False, ncol=5, fontsize=8)

    ax.set_ymargin(0)

    return fig


def observability(data):
    """
    Test the observability of a list of objects for a single date

    Parameters
    ----------
    data : POST data format

        Observatory, date, limits and objects
        data = {
            'observatory' : 'OT',
            'date' : '2020-06-11 00:16:30',
            'date_end' : '2020-06-11 03:44:26',
            'altitude_lower_limit' : '30',
            'altitude_higher_limit' : '90',
            'twilight_type' : 'astronomical',
            'objects' : [{
                    'name' : 'Kelt 8b',
                    'RA' : 283.30551667 ,
                    'Dec' : 24.12738139
                    },
                    (more objects...)
                ]
            }

    Returns
    -------
    observability : dict
        Dictionary with the observability and moon distance for all objects
        {
            'V0879 Cas' : {
                'observability' : 'True', 'moon_separation' : 30.4
            },
            'RU Scl' : {
                'observability' : 'True', 'moon_separation' : 10.8
            }
        }

    """

    import astropy.units as u
    from astroplan import FixedTarget
    from astroplan import (AltitudeConstraint, AtNightConstraint)
    from astroplan import is_observable, is_always_observable

    # Site location
    location = get_location(data['observatory'])

    time_range = Time([data['date'], data['date_end']])

    if 'twilight_type' not in data.keys():
        data['twilight_type'] = 'astronomical'

    if data['twilight_type'] == 'civil':
        twilight_constraint = AtNightConstraint.twilight_civil()
    elif data['twilight_type'] == 'nautical':
        twilight_constraint = AtNightConstraint.twilight_nautical()
    else:
        twilight_constraint = AtNightConstraint.twilight_astronomical()

    # Observation constraints
    constraints = [AltitudeConstraint(int(data['altitude_lower_limit'])*u.deg,
                                      int(data['altitude_higher_limit'])*u.deg),
                                      twilight_constraint
                                      ]

    # Dictionary with star name and observability (bool str)
    result = {}

    # Moon location for the observation date
    middle_observing_time = time_range[-1] - (time_range[-1] - time_range[0])/2
    moon = location.moon_altaz(middle_observing_time)

    for target in data['objects']:
        # Object coordinates
        coords = SkyCoord(ra=target['RA']*u.deg, dec=target['Dec']*u.deg)
        fixed_target = [FixedTarget(coord=coords, name=target['name'])]

        if 'transit' in target.keys():
           time_range = Time([target['transit']['t_early'], target['transit']['t_late']])
           # Are targets *always* observable in the time range?
           observable = is_always_observable(constraints, location, fixed_target, time_range=time_range)
        else:
           time_range = Time([data['date'], data['date_end']])
           # Are targets *ever* observable in the time range?
           observable = is_observable(constraints, location, fixed_target, time_range=time_range)

        moon_separation = moon.separation(coords)

        result[target['name']] = {
                'observable': str(observable[0]),
                'moon_separation': moon_separation.degree
                }

    return result


def observability_dates(data):
    """
    Test the observability of a single objects for several nights

    If the first element of 'dates' contains a single date, then
    the observability is test as *ever* for the night. 
    If a time range is given, observability is test as *always* for the time range

    Parameters
    ----------
    data : POST data format

        # data for transiting planet, time range constrained
        data = {
            'name' : 'Kelt 8b',
            'RA' : 283.30551667 ,
            'Dec' : 24.12738139,
            'observatory' : 'OT',
            'altitude_lower_limit' : '30',
            'altitude_higher_limit' : '90',
            'twilight_type' : 'astronomical',
            'dates' : [
                    ['2020-06-11 00:16:30', '2020-06-11 03:44:26'],
                    ['2020-06-14 06:07:56', '2020-06-14 09:35:53']
                ]
            }
        
        # data for ordinary target, twilight constrained
        # single date list

        data = {
            'name' : 'KIC8012732',
            'RA' : 284.72949583 ,
            'Dec' : 43.86421667,
            'observatory' : 'OT',
            'altitude_lower_limit' : '30',
            'altitude_higher_limit' : '90',
            'dates' : [
                        ['2020-06-11 23:00:00']
                    ]
            }

    Returns
    -------
    observability : dict
        Dictionary with the observability and moon distance for all objects

        {'V0879 Cas' : {
                'observability' : 'True', 'moon_separation' : 30.4
            },
        'RU Scl' : {
                'observability' : 'True', 'moon_separation' : 10.8
            }
        }

    """

    import astropy.units as u
    from astroplan import FixedTarget
    from astroplan import (AltitudeConstraint, AtNightConstraint)
    from astroplan import is_observable, is_always_observable

    # Site location
    location = get_location(data['observatory'])

    coords = SkyCoord(ra=data['RA']*u.deg, dec=data['Dec']*u.deg)
    fixed_target = [FixedTarget(coord=coords, name=data['name'])]    

    # List of dates of observability
    observabilities = []

    if 'twilight_type' not in data.keys():
        data['twilight_type'] = 'astronomical'

    if data['twilight_type'] == 'civil':
        twilight_constraint = AtNightConstraint.twilight_civil()
    elif data['twilight_type'] == 'nautical':
        twilight_constraint = AtNightConstraint.twilight_nautical()
    else:
        twilight_constraint = AtNightConstraint.twilight_astronomical()

    # Observation constraints
    constraints = [AltitudeConstraint(float(data['altitude_lower_limit'])*u.deg,
                                    float(data['altitude_higher_limit'])*u.deg),
                                    twilight_constraint
                ]

    for date in data['dates']:

        # time range for transits
        # Always observable for time range
        if len(data['dates'][0]) > 0:

            # If exoplanet transits, check for observability always during transit,
            # if not, check observability *ever* during night
            time_range = Time([date[0], date[1]])

            # Are targets *always* observable in the time range?
            observable = is_always_observable(constraints, location, fixed_target, time_range=time_range)

        # No time range, *ever* observabable during the night
        else:
            observable = is_observable(constraints, location, fixed_target, times=Time(date[0]))

        # Moon location for the observation date
        moon = location.moon_altaz(Time(date[0]))
        moon_separation = moon.separation(coords)

        observabilities.append({
                'observable': str(observable[0]),
                'moon_separation': moon_separation.degree
                })

    return observabilities


def observability_objects(data):
    """
    Test the observability of a list of objects for a single date

    Parameters
    ----------
    data : POST data format

    data = {
        'observatory' : 'OT',
        'altitude_lower_limit' : '30',
        'altitude_higher_limit' : '90',
        'objects' : [{
                'name' : 'Kelt 8b',
                'RA' : 283.30551667 ,
                'Dec' : 24.12738139,
                'dates' : [
                        ['2020-06-11 00:16:30', '2020-06-11 03:44:26'],
                        ['2020-06-14 06:07:56', '2020-06-14 09:35:53']
                    ]
                },
                {
                    'name' : 'TIC 123456789',
                    'RA' : 13.13055667 ,
                    'Dec' : 24.13912738,
                    'dates' : [
                        ['2020-06-11 23:59:59']
                    ]
                }
            ]
        }

    Returns
    -------
    observability : dict
        Dictionary with the observability and moon distance for all objects

        {'V0879 Cas' : {
                'observability' : 'True', 'moon_separation' : 30.4
            },
        'RU Scl' : {
            'observability' : 'True', 'moon_separation' : 10.8
            }
        }

    """

    import astropy.units as u
    from astroplan import FixedTarget
    from astroplan import (AltitudeConstraint, AtNightConstraint)
    from astroplan import is_observable, is_always_observable

    # Site location
    location = get_location(data['observatory'])

    # dict of observability for each target
    observabilities =  {}

    if 'twilight_type' not in data.keys():
        data['twilight_type'] = 'astronomical'

    if data['twilight_type'] == 'civil':
        twilight_constraint = AtNightConstraint.twilight_civil()
    elif data['twilight_type'] == 'nautical':
        twilight_constraint = AtNightConstraint.twilight_nautical()
    else:
        twilight_constraint = AtNightConstraint.twilight_astronomical()

    # Observation constraints
    constraints = [AltitudeConstraint(float(data['altitude_lower_limit'])*u.deg,
                                      float(data['altitude_higher_limit'])*u.deg),
                                      twilight_constraint
                  ]

    for target in data['objects']:

        coords = SkyCoord(ra=target['RA']*u.deg, dec=target['Dec']*u.deg)
        fixed_target = [FixedTarget(coord=coords, name=target['name'])]    

        observabilities[target['name']] =  []

        for date in target['dates']:

            # time range for transits
            # Always observable for time range
            if len(date) > 1:
                # If exoplanet transit, test observability always during transit,
                # if not, test observability *ever* during night
                time_range = Time([date[0], date[1]])

                # Are targets *always* observable in the time range?
                observable = is_always_observable(constraints, location, fixed_target, time_range=time_range)

            # No time range, *ever* observabable during the night
            else:
                observable = is_observable(constraints, location, fixed_target, times=Time(date[0]))

            # Moon location for the observation date
            moon = location.moon_altaz(Time(date[0]))
            moon_separation = moon.separation(coords)

            observabilities[target['name']].append({
                    'observable': str(observable[0]),
                    'moon_separation': moon_separation.degree
                    })

    return observabilities


def transits(planets, obstime=None, n_eclipses=3):
    """
    Compute next transits for a list of planets

    data = {
        'planets' : {
            'TOI01557.01' : {
                'period' : 0.54348,
                't0' : 2458764.780884,
                'duration' : 0.0912917
            },
            'SDSS' : {
                'period' : 0.0666,
                't0' : 2458986.6912,
                'duration' : 0.0034
            },
        },
        'n_eclipses' : 10,
        'obstime' : '2020-05-28'
    }

    """

    from astroplan import EclipsingSystem 

    if obstime:
        observing_time = Time(obstime)
    else:
        observing_time = Time.now()

    # Dict with transits for all the planets
    planets_transits = {}

    for name, planet in planets.items():

        primary_eclipse_time = Time(planet['t0'], format='jd')
        orbital_period = planet['period'] * u.day
        eclipse_duration = planet['duration'] * u.day

        transits = EclipsingSystem(primary_eclipse_time=primary_eclipse_time,
                                   orbital_period=orbital_period, duration=eclipse_duration,
                                   name=name)

        next_transits = transits.next_primary_eclipse_time(observing_time, n_eclipses=n_eclipses)

        # Transits for this planet
        planet_transits = []
        for transit in next_transits:
            planet_transits.append({
                't_early' : (transit - eclipse_duration / 2).iso,
                't_middle' : transit.iso,
                't_late' : (transit + eclipse_duration / 2).iso
            })

        planets_transits[name] = planet_transits

    return planets_transits


def get_location(observatory=None):
    """Return a Observer object from the observatory name

    Parameters
    ----------
    observatory : str
        Observatory name code: ORM, OT, Paranal, Keck, OAO, CAHA
        Default OT.

    Return
    ------
    location : astroplan.observer.Observer
        If the observatory code is provided, return an Observer object for the observatory,
        in other case return an OrderedDict of the available observatories

    """

    import collections

    locations = collections.OrderedDict({
            "OT" : {"name" : "Observatorio del Teide",
                    "location" : OT_observer()
                   },
            "ORM": {"name" : "Observatorio del Roque de los Muchachos",
                    "location" : Observer.at_site("lapalma")
                   },
            "CAHA": {"name" :  "Calar Alto Observatory",
                    "location" : CAHA_observer()
                   },
            "OAO": {"name" : "Okayama Astrophysical Observatory",
                    "location" : OAO_observer()
                   },
            "Keck": {"name" : "Keck Observatory",
                    "location" : Observer.at_site("Keck Observatory")
                   },
        })

    # If an observatory is indicated, return its Observer object,
    # otherwise return the dict of observatories
    if observatory:
        return locations[observatory]['location']

    return locations




    
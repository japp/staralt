# -*- coding: utf-8 -*-
"""
Staralt main 

@author: japp
"""

__version__ = "0.7 - beta"
__since__ = "2017-11-01"
__updated__ = "2020-10-19"
__author__= "japp <japp@iac.es>"


from flask import Flask, make_response, request
from flask import request, redirect, Response
from flask import render_template, jsonify
import datetime
from sys import exit
import socket

from astropy import units as u
from astropy.coordinates import SkyCoord
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import sys

if sys.version_info.major < 3:
    from urllib2 import urlopen
    from StringIO import StringIO
else:
    from urllib.request import urlopen
    from io import BytesIO as StringIO

# -- END IMPORTS ---------------------------

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
hostname = socket.gethostname()

app = Flask(__name__)

@app.route('/submit', methods=['POST', 'GET'])
def submit():
    """
    staralt form

    """
    import base64
    from io import BytesIO
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from app.staralt import staralt, get_location

    data = {}
    
    # Available locations
    data['locations'] = get_location()

    # Targets list to show in page
    objects_list_str = []

    if request.method == 'POST':

        objects_str = request.form['objects'].strip().split("\r\n")
        observatory = request.form['observatory']

        objects_list = []

        for obj in objects_str:
            obj_info = obj.split(",")
            try:
                if len(obj_info) == 3:
                    c = "{0} {1}".format(obj_info[1], obj_info[2])
                    coordinates = SkyCoord(c, unit=(u.hourangle, u.deg))
                elif len(obj_info) == 1:
                    coordinates = SkyCoord.from_name(obj_info[0])

                if len(obj_info) in [1, 3]:
                    objects_list.append({'name': obj_info[0],
                                        'RA': coordinates.ra.value,
                                        'Dec': coordinates.dec.value})
                else:
                    objects_list_str.append({'name': obj_info[0], 'coords': 'Invalid coordinates'})

                coords = coordinates.to_string('hmsdms', sep=':')
                objects_list_str.append({'name': obj_info[0], 'coords': coords})
                
            except:
                objects_list_str.append({'name': obj_info[0], 'coords': 'Invalid coordinates'})

        # Convierte el string de fecha (YYYY-MM-DD) a objeto date
        date = datetime.datetime.strptime(request.form['date'], "%Y-%m-%d").date()
    else:
        date = datetime.date.today()
        # Teide Observatory by default
        observatory = "OT"
        objects_list = []

    # matplotlib figure
    fig = staralt(observatory, date, objects_list, transits=[])
    canvas = FigureCanvas(fig)
    figfile = BytesIO()
    canvas.print_png(figfile)

    plot = base64.b64encode(figfile.getvalue())
  
    return render_template('submit.html', data=data, plot=plot.decode('utf8'), objects_list=objects_list_str)


@app.route('/', methods=['POST', 'GET'])
def status():
    """
    Return app status

    Returns
    -------
    resp : application/json
        Service status information
  
    """

    data = {
        'name'  : 'staralt-rest',
        'version' : __version__
    }

    resp = jsonify(data)
    resp.status_code = 200

    resp.headers['Link'] = request.base_url 

    return resp


@app.route('/staralt')
@app.route('/staralt/<date>/<observatory>', methods=['GET'])
def staralt(date=None, observatory='OT'):
    """
    Create a basic altitude plot for the indicated date. Location is OT.

    Parameters
    ----------
    date : str format YYYY-MM-DD
        Observation date.
    observatory : str
        Observation code, from the locations available at staralt.get_location.
        Default OT.

    Returns
    -------
    response : image/png
        Altitude plot in png format

    """

    from app.staralt import staralt
    import pytz

    if not date:
        # Current date
        date = datetime.datetime.now(pytz.UTC).date()
    else:
        # Convert date str YYYY-MM-DD to datatime.date
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        # Add UTC timezone to date
        date = date.replace(tzinfo=pytz.UTC)

    # matplotlib figure
    fig = staralt(observatory, date, [])

    canvas = FigureCanvas(fig)

    output = StringIO()

    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'

    return response


@app.route('/altitudeplot', methods=['POST', 'GET'])
def plot():
    """
    ReST service for an altitude plot
    """
    

    # POST data from client, converted to json
    data = request.get_json(silent=True)

    from app.staralt import staralt

    # Convierte el string de fecha (YYYY-MM-DD) a objeto date
    date = datetime.datetime.strptime(data['date'][:10], "%Y-%m-%d").date()

    # matplotlib figure
    if 'transits' in data.keys():
        transits = data['transits']
    else:
        transits = []
    
    if 'twilight' in data.keys():
        twilight = data['twilight']
    else:
        twilight = 'astronomical'

    fig = staralt(data['observatory'], date, data['objects'], transits, twilight)

    canvas = FigureCanvas(fig)

    output = StringIO()

    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'

    return response


@app.route('/observability', methods=['POST', 'GET'])
def observability():
    """
    ReST service to test observability for multiple targets for a single date

    Deprecated since v0.5. Use /observability_dates or /observability_objects
    """

    from app.staralt import observability

    # POST data from client, converted to json
    data = request.get_json(silent=True)
    objects_observability = observability(data)

    return jsonify(objects_observability)


@app.route('/observability_dates', methods=['POST', 'GET'])
def observability_dates():
    """
    ReST service to test observability for multiple dates
    """

    from app.staralt import observability_dates

    # POST data from client, converted to json
    data = request.get_json(silent=True)
    objects_observability = observability_dates(data)

    return jsonify(objects_observability)


@app.route('/observability_objects', methods=['POST', 'GET'])
def observability_objects():
    """
    ReST service to test observability for multiple targets
    """

    from app.staralt import observability_objects

    # POST data from client, converted to json
    data = request.get_json(silent=True)
    objects_observability = observability_objects(data)

    return jsonify(objects_observability)


@app.route('/transits', methods=['POST', 'GET'])
def transits():
    """
    ReST service for exoplanetary transits
    """

    from app.staralt import transits

    # POST data from client, converted to json
    data = request.get_json(silent=True)
    transits = transits(data['planets'], data['obstime'], data['n_eclipses'])

    return jsonify(transits)


if __name__ == '__main__':

    if hostname == "carlota":
        host = "carlota"
        port = 5000
        debug = True
    else:
        host = "localhost"
        port = 5000
        debug = True

    app.run(debug=debug, host=host, port=port)

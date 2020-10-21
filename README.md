# staralt-rest

ReST service for astronomical objects observability and altitude plots.

**Version:** 0.7 - Beta

Find some documentation at `docs/`. To update the documentation get into that directory and do `make html`.

* [Guía Sphinx-apidoc Guide](https://medium.com/@eikonomega/getting-started-with-sphinx-autodoc-part-1-2cebbbca5365)
* [Markdown guide](https://guides.github.com/features/mastering-markdown/)
* [reStructuredText guide](https://www.sphinx-doc.org/es/master/usage/restructuredtext/basics.html)

## Dependencies

* Flask
* matplotlib
* astropy
* astroplan

## Installation

Get into the package directory and do:

```bash
python setup.py install
```
or

```bash
pip3 install . [--user]
```

## Start up

In debug mode, just launch the Flask microserver. Change the servername and port (5000 default) in `run.py`. 

```bash
$ ./run.py
```

In production, use the wsgi module with `staralt-rest.wsgi` as guide. 

## Basic use

`staralt-rest` is a ReST service, so it is designed to be used by external applications using http protocol and JSON format. In addition, it includes some basic web-basic tools.

Here are some use examples in Python, but it can be done with any programing language having HTTP GET implementation. 

Test the observability for a list of targets:

```python
import requests

server = "https://www.example.com/staralt"

targets = [
    {
    'name': 'Cor Caroli',
    'RA': 194.00482,
    'Dec': +38.31629
    },
    {
    'name': 'NGC 1245 cluster',
    'RA': 048.70594,
    'Dec': 47.23869
    },
    {
    'name': 'Zubeneschamali',
    'RA': 229.24831,
    'Dec': -9.382914
    }


observability = requests.post(server + '/observability', json={"observatory": "Keck", 
                                                    "date": "2020-11-21 22:00",
                                                    "date_end": "2020-11-22 06:00",
                                                    "altitude_lower_limit": 30,
                                                    "altitude_higher_limit": 90,
                                                    "twilight_type" : "astronomical",
                                                    "objects": targets
                                                    }
                    )


print(observability.content)
```

Returning a json-like string

```json
{
    'Cor Caroli' : {
        'observability' : 'True', 'moon_separation' : 30.4
    },
    'NGC 1245 cluster' : {
        'observability' : 'True', 'moon_separation' : 10.8
    },
    'Zubeneschamali' : {
        'observability' : 'False', 'moon_separation' : 110.5
    }
}
```

Create an altitude plot for a list of targets

```python

def save_image(image):
    fout = open("staralt.png", "wb")
    fout.write(image)
    fout.close()

image = requests.post(server + '/altitudeplot', json={"observatory": "OT", 
                                                    "date": "2020-09-28",
                                                    "objects": targets
                                                    }
                    )

save_image(image.content)
```


## Basic ReST services

ReST status of the service in JSON. 

```
  /
```

Returns:

```
{
  "name": "staralt-rest", 
  "version": "0.7 - beta"
}
```

ReST service to test the observability of a list of objects for a single date

```
  /observability
```


ReST service to test the observability of a single objects for several nights

```
  /observability_dates
```

ReST service to test the observability of a list of objects for a single date

```
  /observability_objects
```

ReST service to compute next transits for a list of planets

```
  /transits
```

## Web based tools

Basic web form for targets observability. 

```
  /submit
```


PNG altitude plot for the current or specific date, without targets. 

```
  /staralt
  /staralt/2021-10-08
```


## TODO, known bugs

  * Fix time axis on DST shift day 


## Change log

### Version 0.7 beta

* x-axis now indicates local time, including DST. Locations are now timezone aware.
* New second x-axis labels line with UT
* Minor bug fix

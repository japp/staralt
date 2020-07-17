# staralt-rest

ReST service for astronomical objects observability and altitude plots.

** Version:** 0.5 - Beta

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

  python setup.py install

or

  pip3 install . [--user]

## Start up

In debug mode, just launch the Flask microserver. Change the servername and port (5000 default) in `run.py`. 

```bash
  $ ./run.py
```

In production, use the wsgi module with `staralt-rest.wsgi` as guide. 

## Basic use

Test the observability of a list of objects for a single date

  /observability

Test the observability of a single objects for several nights

  /observability_dates

Test the observability of a list of objects for a single date

  /observability_objects

Compute next transits for a list of planets

  /transits

Basic web form for targets observability

  /submit

PNG altitude plot 

  /staralt


## TODO

  * Several things...
  * 
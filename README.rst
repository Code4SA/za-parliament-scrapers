za-parliament-scrapers
======================

.. image:: https://badge.fury.io/py/za-parliament-scrapers.svg
    :target: http://badge.fury.io/py/za-parliament-scrapers

.. image:: https://travis-ci.org/Code4SA/za-parliament-scrapers.svg
    :target: http://travis-ci.org/Code4SA/za-parliament-scrapers

This is a collection of scrapers for working with data from the
`Parliament of South Africa <http://www.parliament.gov.za/>`_. It includes:

1. Scrapers for handling Questions and Replies documents

Credit
------

Most of the Question and Replies scraping was taken from https://github.com/mysociety/za-hansard.

Installation
------------

Install using::

    pip install za-parliament-scrapers

Development
-----------

Clone the repo and setup for local development::

    pip install -e .[dev]

To run tests::

    nosetest --with-doctest && flake8 za_parliament_scrapers

License
-------

`MIT License <LICENSE>`_

# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='Fibra',
    version='0.3',
    author = 'Augusto Roccasalva',
    author_email = 'augusto@rioplomo.com.ar',
    url = 'http://github.com/coyotevz/fibra',
    description = 'Simple Web Based Customer Accounts Tracker',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Point-Of-Sale',
    ],
    platforms = "any",
    license = 'BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'psycopg2', # PostgreSQL driver
        'gunicorn',
        'Flask', # require werkzeug, jinja2
        'Flask-SQLAlchemy', # require sqlalchemy
        'Flask-WTF', # require wtforms
        'Flask-Script',
        'Flask-Assets', # require webassets
        'cssmin',
        'pyScss',
    ],
)

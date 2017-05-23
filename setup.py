# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='Fibra',
    version='0.2',
    author = 'Augusto Roccasalva',
    author_email = 'augusto@rocctech.com.ar',
    url = 'http://dev.rocctech.com.ar/projects/fibra',
    description = 'Simple Web Based Customer Accounts Tracker',
    download_url = 'http://dev.rocctech.com.ar/projects/fibra/wiki/Downloads',
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
    entry_points = """\
    [console_scripts]
    fibra = fibra.commands:main
    """
)

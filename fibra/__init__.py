# -*- coding: utf-8 -*-

import os
from os import path
import locale

locale.setlocale(locale.LC_ALL, '')

from flask import Flask
from flask.ext.assets import Environment, Bundle

from fibra.models import db
import fibra.scssfilter # webasset filter
from fibra.jinjafilters import dateformat_filter, timeago_filter, moneyfmt_filter

app = Flask(__name__)

# Config
if os.getenv('DEV') == 'yes':
    app.config.from_object('fibra.config.DevelopmentConfig')
    app.logger.info("Config: Development")
elif os.getenv('TEST') == 'yes':
    app.config.from_object('fibra.config.TestConfig')
    app.logger.info("Config: Test")
else:
    app.config.from_object('fibra.config.ProductionConfig')
    app.logger.info("Config: Production")

# Jinja2 extensions
app.jinja_options['extensions'].extend([
    'jinja2.ext.i18n',
    'jinja2.ext.do',
    'jinja2.ext.loopcontrols',
])

# Jinja2 filters
app.jinja_env.filters['dateformat'] = dateformat_filter
app.jinja_env.filters['timeago'] = timeago_filter
app.jinja_env.filters['moneyfmt'] = moneyfmt_filter


# Flask-Assets
assets = Environment(app)
assets_out_dir = app.config.get('ASSETS_OUTPUT_DIR')
# ensure output directory exists
if not path.exists(path.join(app.static_folder, assets_out_dir)):
    app.logger.info("Creating assets output folder")
    os.mkdir(path.join(app.static_folder, assets_out_dir))

# webassets bundles

jquery_bundle = Bundle(
    'js/libs/jquery-1.7.js',
    'js/libs/ui/jquery.ui.core.js',
    'js/libs/ui/jquery.ui.datepicker.js',
    'js/libs/ui/jquery.ui.datepicker-es.js',
    'js/libs/ui/jquery.effects.core.js',
    'js/libs/ui/jquery.effects.drop.js',
)

js_bundle = Bundle(
    jquery_bundle,
    'js/plugins/jshashtable.js',
    'js/plugins/jquery.numberformatter.js',
    'js/plugins/jquery.calculation.js',
    'js/plugins/jquery.autoresize.js',
    'js/plugins/jquery.tools.tooltip.js',
    'js/plugins/jquery.tools.tooltip.slide.js',
    'js/plugins/date.js',
    'js/plugins/jquery.message.js',
    'js/plugins/jquery.ajaxQueue.js',
    'js/plugins/jquery.autocomplete.js',
    'js/plugins/jquery.select.autocomplete.js',
    'js/plugins/jquery.cookie.js',
    'js/script.js',
    filters='jsmin',
    output=path.join(assets_out_dir, 'js_bundle.js')
)

scss_bundle = Bundle(
    'scss/master.scss',
    'scss/forms.scss',
    'scss/dateinput.scss',
    'scss/list.scss',
    'scss/buttons.scss',
    'scss/icons.scss',
    filters='apyscss',
    #filters='scss',
    output=path.join(assets_out_dir, 'style_bundle.css'),
    debug=False,
)

css_bundle = Bundle(
    'css/reset.css',
    'fonts/meta-web-pro.css',
    'fonts/droid.css',
    scss_bundle,
    filters='cssmin',
    output=path.join(assets_out_dir, 'css_bundle.css'),
)

assets.register('js_bundle', js_bundle)
assets.register('css_bundle', css_bundle)

# Database
db.init_app(app)

import fibra.views

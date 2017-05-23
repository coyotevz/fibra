# -*- coding: utf-8 -*-

from flask import current_app, request, json

def render_json(*args):

    kwargs = dict(indent=None if request.is_xhr else 2)
    return current_app.response_class(
                    json.dumps(*args, **kwargs),
                    mimetype='application/json')

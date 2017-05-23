# -*- coding: utf-8 -*-

import click
from fibra import app

@app.cli.command()
def initdb():
    """Creates database tables"""
    from fibra.models import db
    db.create_all(app=app)


@app.cli.command()
def dropdb():
    """Drops all database tables"""
    from fibra.models import db
    if click.confirm("Are you sure ? You will lose all your data"):
        db.drop_all()

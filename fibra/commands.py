# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from fibra import app

manager = Manager(app)


@manager.command
def initdb():
    from fibra.models import db
    db.create_all(app=app)


def main():
    manager.run()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

from os import path
from webassets.filter import Filter, register_filter

__all__ = ('PySCSSFilter',)


class PySCSSFilter(Filter):
    """Compiles `Scss <http://sass-lang.org/>`_ markup to real CSS.

    Requires the ``pyScss`` package (http://pypi.python.org/pypi/pyScss/).
    Run:
        $ pip install pyScss
    """

    name = 'apyscss'

    def setup(self):
        try:
            from scss.compiler import Compiler
        except ImportError:
            raise EnvironmentError('The "pyScss" package is not installed.')
        else:

            search_path = [
                path.join(path.abspath(path.dirname(__file__)), 'static', 'scss')
            ]
            self.compiler = Compiler(search_path=search_path)

    def input(self, _in, out, **kw):
        out.write(self.compiler.compile_string(_in.read()))

register_filter(PySCSSFilter)

# -*- coding: utf-8 -*-

import locale
locale.setlocale(locale.LC_ALL, '')

from datetime import date
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from sqlalchemy import func
from werkzeug.datastructures import Headers
from werkzeug.wsgi import wrap_file
from flask import current_app, request

from fibra.models import Invoice, db
from fibra.jinjafilters import moneyfmt_filter
from fibra.fpdf import FPDF

date_fmt = '%d/%m/%Y'


class Report(FPDF):
    filename = 'report.pdf'
    title = u'Reporte Genérico'
    side_margin = 15
    top_margin = 10

    def __init__(self, *args, **kwargs):
        FPDF.__init__(self)
        self.args = args
        self.kwargs = kwargs
        self.setup()
        self.render()

    def setup(self):
        self.set_creator(_e('Fibra 0.1'))
        self.set_title(_e(self.title))
        self.set_margins(self.side_margin, self.top_margin)
        self.alias_nb_pages()
        self.add_page()

    def hline(self):
        self.ln(1)
        self.line(self.x, self.y, self.x+180, self.y)
        self.ln(1)

    def header(self):
        self.set_font('Arial', '', 9)
        x, y = self.x, self.y
        self.cell(180, 4, txt=_e(date.today().strftime('%d de %B, %Y')), align='R')
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=_e(self.title), align='C', ln=1)
        self.ln(7)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.cell(180, 4, txt=_e('Hoja %s de {nb}' % self.page_no()), align='C')

    def invoice_line(self, invoice):

        if invoice.state == u'PAID':
            self.set_text_color(128, 128, 128)
            state_view = u'Pagada (%s)' % invoice.cancelled_date.strftime(date_fmt)
            state_align = 'C'
            balance = invoice.total
        else:
            self.set_text_color(0, 0, 0)
            state_view = u''
            state_align = 'L'
            balance = invoice.balance
            if invoice.state == u'EXPIRED':
                state_view = u'VENCIDA'

        self.set_font('Arial', 'B', 10)
        self.cell(45, 4, txt=_e(invoice.fulldesc))
        self.set_font('Arial', '', 10)
        self.cell(35, 4, txt=_e(invoice.issue_date.strftime(date_fmt)))
        self.cell(35, 4, txt=_e(invoice.expiration_date.strftime(date_fmt)))
        self.cell(30, 4, txt=_e(state_view), align=state_align)
        self.cell(35, 4, txt=_e(moneyfmt_filter(balance)), align='R', ln=1)

    def customer_header(self, customer, extended=False):
        self.set_font('Arial', 'B', 12)
        self.cell(180, 4, txt=_e(customer.name), ln=1)
        if extended:
            self.customer_extend(customer)
        self.hline()

    def customer_extend(self, customer):
        self.set_font('Arial', '', 10)
        x, y = self.x, self.y
        self.cell(180, 4, txt=_e(customer.address))
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=_e(customer.cuit), align='R', ln=1)


    def customer_balance(self, balance):
        self.hline()
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=_e(moneyfmt_filter(balance, curr='$ ')), align='R')
        self.ln(7)

    def render(self):
        raise NotImplementedError('You must implement this method in your own subclass')

    def response(self):
        stream = StringIO()
        stream.write(self.output(dest='S'))
        length = stream.tell()
        stream.seek(0)

        headers = Headers()
        headers.add('Content-Disposition', 'attachment', filename=self.filename)
        headers.add('Content-Length', length)

        data = wrap_file(request.environ, stream)
        rv = current_app.response_class(data, mimetype='application/pdf', headers=headers,
                                        direct_passthrough=True)
        return rv


_states = [u'PENDING', u'EXPIRED']

class GeneralReport(Report):
    filename = 'general_report.pdf'
    title = u'Informe de Cuentas Corrientes'

    def render(self):
        query = self.kwargs.get('query', None)
        if not query:
            raise ValueError('You must provide a valid query to constructor')
        for customer in query:
            self.customer_header(customer)
            for invoice in customer.invoices.filter(Invoice.state.in_(_states))\
                                            .order_by(Invoice.expiration_date.asc()):
                self.invoice_line(invoice)
            self.customer_balance(customer.balance)


class CustomerReport(Report):
    filename = 'customer_report.pdf'
    title = u'Informe de Cuenta Corriente'

    def render(self):
        customer = self.kwargs.get('customer', None)
        if not customer:
            raise ValueError('You must provide a valid customer to constructor')

        self.customer_header(customer, extended=True)
        for invoice in customer.invoices.filter(Invoice.state.in_(_states))\
                                        .order_by(Invoice.expiration_date.asc()):
            self.invoice_line(invoice)
        self.customer_balance(customer.balance)

        if self.kwargs.get('detailed', True):
            for invoice in customer.invoices.filter(Invoice.state==u'PAID')\
                                            .order_by(Invoice.expiration_date.desc()):
                self.invoice_line(invoice)
            payed = db.session.query(func.sum(Invoice.total))\
                              .filter(Invoice.customer==customer)\
                              .filter(Invoice.state==u'PAID')\
                              .scalar()
            if payed:
                self.set_draw_color(128, 128, 128)
                self.customer_balance(payed)
                self.set_draw_color(0, 0, 0)
                self.set_text_color(0, 0, 0)



# from pyPDF (https://github.com/mfenniak/pyPdf/blob/trunk/pyPdf/generic.py#L736)
#
# Copyright (c) 2006, Mathieu Fenniak
# All rights reserved.
#

def encode_pdfdocencoding(unicode_string):
    retval = ''
    for c in unicode_string:
        try:
            retval += chr(_pdfDocEncoding_rev[c])
        except KeyError:
            raise UnicodeEncodeError('pdfdocencoding', c, -1, -1, 'does not exists in tranlation table')
    return retval

_e = encode_pdfdocencoding


_pdfDocEncoding = (
  u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000',
  u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000',
  u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000', u'\u0000',
  u'\u02d8', u'\u02c7', u'\u02c6', u'\u02d9', u'\u02dd', u'\u02db', u'\u02da', u'\u02dc',
  u'\u0020', u'\u0021', u'\u0022', u'\u0023', u'\u0024', u'\u0025', u'\u0026', u'\u0027',
  u'\u0028', u'\u0029', u'\u002a', u'\u002b', u'\u002c', u'\u002d', u'\u002e', u'\u002f',
  u'\u0030', u'\u0031', u'\u0032', u'\u0033', u'\u0034', u'\u0035', u'\u0036', u'\u0037',
  u'\u0038', u'\u0039', u'\u003a', u'\u003b', u'\u003c', u'\u003d', u'\u003e', u'\u003f',
  u'\u0040', u'\u0041', u'\u0042', u'\u0043', u'\u0044', u'\u0045', u'\u0046', u'\u0047',
  u'\u0048', u'\u0049', u'\u004a', u'\u004b', u'\u004c', u'\u004d', u'\u004e', u'\u004f',
  u'\u0050', u'\u0051', u'\u0052', u'\u0053', u'\u0054', u'\u0055', u'\u0056', u'\u0057',
  u'\u0058', u'\u0059', u'\u005a', u'\u005b', u'\u005c', u'\u005d', u'\u005e', u'\u005f',
  u'\u0060', u'\u0061', u'\u0062', u'\u0063', u'\u0064', u'\u0065', u'\u0066', u'\u0067',
  u'\u0068', u'\u0069', u'\u006a', u'\u006b', u'\u006c', u'\u006d', u'\u006e', u'\u006f',
  u'\u0070', u'\u0071', u'\u0072', u'\u0073', u'\u0074', u'\u0075', u'\u0076', u'\u0077',
  u'\u0078', u'\u0079', u'\u007a', u'\u007b', u'\u007c', u'\u007d', u'\u007e', u'\u0000',
  u'\u2022', u'\u2020', u'\u2021', u'\u2026', u'\u2014', u'\u2013', u'\u0192', u'\u2044',
  u'\u2039', u'\u203a', u'\u2212', u'\u2030', u'\u201e', u'\u201c', u'\u201d', u'\u2018',
  u'\u2019', u'\u201a', u'\u2122', u'\ufb01', u'\ufb02', u'\u0141', u'\u0152', u'\u0160',
  u'\u0178', u'\u017d', u'\u0131', u'\u0142', u'\u0153', u'\u0161', u'\u017e', u'\u0000',
  u'\u20ac', u'\u00a1', u'\u00a2', u'\u00a3', u'\u00a4', u'\u00a5', u'\u00a6', u'\u00a7',
  u'\u00a8', u'\u00a9', u'\u00aa', u'\u00ab', u'\u00ac', u'\u0000', u'\u00ae', u'\u00af',
  u'\u00b0', u'\u00b1', u'\u00b2', u'\u00b3', u'\u00b4', u'\u00b5', u'\u00b6', u'\u00b7',
  u'\u00b8', u'\u00b9', u'\u00ba', u'\u00bb', u'\u00bc', u'\u00bd', u'\u00be', u'\u00bf',
  u'\u00c0', u'\u00c1', u'\u00c2', u'\u00c3', u'\u00c4', u'\u00c5', u'\u00c6', u'\u00c7',
  u'\u00c8', u'\u00c9', u'\u00ca', u'\u00cb', u'\u00cc', u'\u00cd', u'\u00ce', u'\u00cf',
  u'\u00d0', u'\u00d1', u'\u00d2', u'\u00d3', u'\u00d4', u'\u00d5', u'\u00d6', u'\u00d7',
  u'\u00d8', u'\u00d9', u'\u00da', u'\u00db', u'\u00dc', u'\u00dd', u'\u00de', u'\u00df',
  u'\u00e0', u'\u00e1', u'\u00e2', u'\u00e3', u'\u00e4', u'\u00e5', u'\u00e6', u'\u00e7',
  u'\u00e8', u'\u00e9', u'\u00ea', u'\u00eb', u'\u00ec', u'\u00ed', u'\u00ee', u'\u00ef',
  u'\u00f0', u'\u00f1', u'\u00f2', u'\u00f3', u'\u00f4', u'\u00f5', u'\u00f6', u'\u00f7',
  u'\u00f8', u'\u00f9', u'\u00fa', u'\u00fb', u'\u00fc', u'\u00fd', u'\u00fe', u'\u00ff'
)

assert len(_pdfDocEncoding) == 256

_pdfDocEncoding_rev = {}
for i in range(256):
    char = _pdfDocEncoding[i]
    if char == u"\u0000":
        continue
    assert char not in _pdfDocEncoding_rev
    _pdfDocEncoding_rev[char] = i

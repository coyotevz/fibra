# -*- coding: utf-8 -*-

import locale
locale.setlocale(locale.LC_ALL, '')

from datetime import date
from io import StringIO

from sqlalchemy import func
from werkzeug.datastructures import Headers
from werkzeug.wsgi import wrap_file
from flask import current_app, request

from fibra.models import Invoice, db
from fibra.jinjafilters import moneyfmt_filter

from fpdf import FPDF

date_fmt = '%d/%m/%Y'


class Report(FPDF):
    filename = 'report.pdf'
    title = 'Reporte Genérico'
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

        if invoice.state == 'PAID':
            self.set_text_color(128, 128, 128)
            state_view = 'Pagada (%s)' % invoice.cancelled_date.strftime(date_fmt)
            state_align = 'C'
            balance = invoice.total
        else:
            self.set_text_color(0, 0, 0)
            state_view = ''
            state_align = 'L'
            balance = invoice.balance
            if invoice.state == 'EXPIRED':
                state_view = 'VENCIDA'

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


_states = ['PENDING', 'EXPIRED']

class GeneralReport(Report):
    filename = 'general_report.pdf'
    title = 'Informe de Cuentas Corrientes'

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
    title = 'Informe de Cuenta Corriente'

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
            for invoice in customer.invoices.filter(Invoice.state=='PAID')\
                                            .order_by(Invoice.expiration_date.desc()):
                self.invoice_line(invoice)
            payed = db.session.query(func.sum(Invoice.total))\
                              .filter(Invoice.customer==customer)\
                              .filter(Invoice.state=='PAID')\
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
  '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000',
  '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000',
  '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000', '\u0000',
  '\u02d8', '\u02c7', '\u02c6', '\u02d9', '\u02dd', '\u02db', '\u02da', '\u02dc',
  '\u0020', '\u0021', '\u0022', '\u0023', '\u0024', '\u0025', '\u0026', '\u0027',
  '\u0028', '\u0029', '\u002a', '\u002b', '\u002c', '\u002d', '\u002e', '\u002f',
  '\u0030', '\u0031', '\u0032', '\u0033', '\u0034', '\u0035', '\u0036', '\u0037',
  '\u0038', '\u0039', '\u003a', '\u003b', '\u003c', '\u003d', '\u003e', '\u003f',
  '\u0040', '\u0041', '\u0042', '\u0043', '\u0044', '\u0045', '\u0046', '\u0047',
  '\u0048', '\u0049', '\u004a', '\u004b', '\u004c', '\u004d', '\u004e', '\u004f',
  '\u0050', '\u0051', '\u0052', '\u0053', '\u0054', '\u0055', '\u0056', '\u0057',
  '\u0058', '\u0059', '\u005a', '\u005b', '\u005c', '\u005d', '\u005e', '\u005f',
  '\u0060', '\u0061', '\u0062', '\u0063', '\u0064', '\u0065', '\u0066', '\u0067',
  '\u0068', '\u0069', '\u006a', '\u006b', '\u006c', '\u006d', '\u006e', '\u006f',
  '\u0070', '\u0071', '\u0072', '\u0073', '\u0074', '\u0075', '\u0076', '\u0077',
  '\u0078', '\u0079', '\u007a', '\u007b', '\u007c', '\u007d', '\u007e', '\u0000',
  '\u2022', '\u2020', '\u2021', '\u2026', '\u2014', '\u2013', '\u0192', '\u2044',
  '\u2039', '\u203a', '\u2212', '\u2030', '\u201e', '\u201c', '\u201d', '\u2018',
  '\u2019', '\u201a', '\u2122', '\ufb01', '\ufb02', '\u0141', '\u0152', '\u0160',
  '\u0178', '\u017d', '\u0131', '\u0142', '\u0153', '\u0161', '\u017e', '\u0000',
  '\u20ac', '\u00a1', '\u00a2', '\u00a3', '\u00a4', '\u00a5', '\u00a6', '\u00a7',
  '\u00a8', '\u00a9', '\u00aa', '\u00ab', '\u00ac', '\u0000', '\u00ae', '\u00af',
  '\u00b0', '\u00b1', '\u00b2', '\u00b3', '\u00b4', '\u00b5', '\u00b6', '\u00b7',
  '\u00b8', '\u00b9', '\u00ba', '\u00bb', '\u00bc', '\u00bd', '\u00be', '\u00bf',
  '\u00c0', '\u00c1', '\u00c2', '\u00c3', '\u00c4', '\u00c5', '\u00c6', '\u00c7',
  '\u00c8', '\u00c9', '\u00ca', '\u00cb', '\u00cc', '\u00cd', '\u00ce', '\u00cf',
  '\u00d0', '\u00d1', '\u00d2', '\u00d3', '\u00d4', '\u00d5', '\u00d6', '\u00d7',
  '\u00d8', '\u00d9', '\u00da', '\u00db', '\u00dc', '\u00dd', '\u00de', '\u00df',
  '\u00e0', '\u00e1', '\u00e2', '\u00e3', '\u00e4', '\u00e5', '\u00e6', '\u00e7',
  '\u00e8', '\u00e9', '\u00ea', '\u00eb', '\u00ec', '\u00ed', '\u00ee', '\u00ef',
  '\u00f0', '\u00f1', '\u00f2', '\u00f3', '\u00f4', '\u00f5', '\u00f6', '\u00f7',
  '\u00f8', '\u00f9', '\u00fa', '\u00fb', '\u00fc', '\u00fd', '\u00fe', '\u00ff'
)

assert len(_pdfDocEncoding) == 256

_pdfDocEncoding_rev = {}
for i in range(256):
    char = _pdfDocEncoding[i]
    if char == "\u0000":
        continue
    assert char not in _pdfDocEncoding_rev
    _pdfDocEncoding_rev[char] = i

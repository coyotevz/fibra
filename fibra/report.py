# -*- coding: utf-8 -*-

from datetime import date

from sqlalchemy import func
from flask import make_response

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
        self.set_creator('Fibra 0.3')
        self.set_title(self.title)
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
        self.cell(180, 4, txt=date.today().strftime('%d de %B, %Y'), align='R')
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=self.title, align='C', ln=1)
        self.ln(7)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.cell(180, 4, txt='Hoja %s de {nb}' % self.page_no(), align='C')

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
        self.cell(45, 4, txt=invoice.fulldesc)
        self.set_font('Arial', '', 10)
        self.cell(35, 4, txt=invoice.issue_date.strftime(date_fmt))
        self.cell(35, 4, txt=invoice.expiration_date.strftime(date_fmt))
        self.cell(30, 4, txt=state_view, align=state_align)
        self.cell(35, 4, txt=moneyfmt_filter(balance), align='R', ln=1)

    def customer_header(self, customer, extended=False):
        self.set_font('Arial', 'B', 12)
        self.cell(180, 4, txt=customer.name, ln=1)
        if extended:
            self.customer_extend(customer)
        self.hline()

    def customer_extend(self, customer):
        self.set_font('Arial', '', 10)
        x, y = self.x, self.y
        self.cell(180, 4, txt=customer.address)
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=customer.cuit, align='R', ln=1)

    def customer_balance(self, balance):
        self.hline()
        self.set_font('Arial', 'B', 10)
        self.cell(180, 4, txt=moneyfmt_filter(balance, curr='$ '),
                  align='R')
        self.ln(7)

    def render(self):
        raise NotImplementedError("You must implement this method in your own "
                                  "subclass")

    def response(self):
        resp = make_response(self.output(dest='S').encode('latin-1'))
        resp.headers.set('Content-Disposition', 'attachment',
                         filename=self.filename)
        resp.headers.set('Content-Type', 'application/pdf')
        return resp


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
            for inv in customer.invoices.filter(Invoice.state.in_(_states))\
                               .order_by(Invoice.expiration_date.asc()):
                self.invoice_line(inv)
            self.customer_balance(customer.balance)


class CustomerReport(Report):
    filename = 'customer_report.pdf'
    title = 'Informe de Cuenta Corriente'

    def render(self):
        customer = self.kwargs.get('customer', None)
        if not customer:
            raise ValueError("You must provide valid customer to constructor")

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

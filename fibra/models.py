# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy

from fibra.sqla import Numeric

db = SQLAlchemy()
# Patch custom implementation for sqlite backend
db.Numeric = Numeric


STATES = {
    'EXPIRED': 1,
    'PENDING': 2,
    'PAID':    3,
}


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __repr__ (self):
        return '<User %r>' % self.username


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text)
    cuit = db.Column(db.Text)
    notes = db.Column(db.Text)
    contacts = db.relationship('Contact', backref='customer', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')

    def __repr__(self):
        return '<Customer %r>' % self.name

    def get_balance(self, state=None):
        if not state:
            invoices = self.invoices.filter(Invoice.state.in_(['PENDING', 'EXPIRED']))
        else:
            invoices = self.invoices.filter(Invoice.state==state)
        return sum([i.balance for i in invoices]) or Decimal(0)

    balance = property(get_balance)

    @hybrid_property
    def state(self):
        s = 'PAID'
        for i in self.invoices.filter(Invoice.state.in_(['PENDING', 'EXPIRED'])):
            i._check_state()
        if self.invoices.filter(Invoice.state=='PENDING').count() > 0:
            s = 'PENDING'
        if self.invoices.filter(Invoice.state=='EXPIRED').count() > 0:
            s = 'EXPIRED'
        return s

    @state.expression
    def state(self):
        return Invoice.state

    @classmethod
    def get_debtors(cls):
        return cls.query.join(Invoice).filter(Invoice.state.in_(['PENDING', 'EXPIRED']))

    @property
    def next_expiration(self):
        rv = date.max
        next_invoice = self.invoices.filter(Invoice.state.in_(['PENDING', 'EXPIRED']))\
                                    .order_by(Invoice.expiration_date.asc()).first()
        if next_invoice:
            rv = next_invoice.expiration_date
        return rv

    def count_invoices(self, states=['PENDING', 'EXPIRED']):
        return self.invoices.filter(Invoice.state.in_(states)).count()


class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text)
    phone = db.Column(db.Text)
    mail = db.Column(db.Text)
    role = db.Column(db.Text)
    notes = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'),
                            nullable=False, index=True)

    @property
    def name(self):
        return " ".join([self.first_name, self.last_name])

    def __repr__(self):
        return '<Contact %r>' % self.name


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, nullable=False)
    point_sale = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    _state = db.Column("state", db.Enum('EXPIRED', 'PENDING', 'PAID', name='State'), default='PENDING')
    issue_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    notes = db.Column(db.UnicodeText)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'),
                            nullable=False, index=True)
    invoice_payments = db.relationship('InvoicePayment', cascade="all, delete-orphan", backref="invoice")

    payments = association_proxy('invoice_payments', 'payment')

    def add_payment(self, payment, amount=None):
        if amount is None:
            amount = min([payment.amount, self.balance])
        self.invoice_payments.append(InvoicePayment(payment, amount))

    @property
    def fulldesc(self):
        return "%s %04d-%08d" % (self.type, self.point_sale, self.number)

    @property
    def cancelled_date(self):
        if self.state in ('PENDING', 'EXPIRED'):
            return None
        return Payment.query.join('invoice_payments')\
                            .filter(InvoicePayment.invoice==self)\
                            .order_by(Payment.date.desc())[0].date

    @hybrid_property
    def state(self):
        if self._state in ('PENDING', 'EXPIRED'):
            self._check_expired()
            self._check_paid()
            db.session.commit()
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def _check_state(self):
        if self._state in ('PENDING', 'EXPIRED'):
            self._check_expired()
            self._check_paid()
            db.session.commit()

    def _check_expired(self):
        if self._state == 'PENDING' and self.expiration_date < date.today():
            self._state = 'EXPIRED'

    def _check_paid(self):
        if InvoicePayment.query.filter(InvoicePayment.invoice==self).count() > 0:
            if self.balance <= Decimal(0):
                self._state = 'PAID'

    @property
    def balance(self):
        paid = db.session.query(func.sum(InvoicePayment.amount))\
                         .filter(InvoicePayment.invoice==self).scalar() or Decimal(0)
        return self.total - paid


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    receipt_number = db.Column(db.Integer, unique=True)
    notes = db.Column(db.Text)

    invoices = association_proxy('invoice_payments', 'invoice')

    def add_invoices(self, invoices):
        for invoice in invoices:
            invoice.add_payment(self)

class InvoicePayment(db.Model):
    __tablename__ = 'invoice_payment'
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment = db.relationship(Payment, lazy='joined', backref='invoice_payments')

    def __init__(self, payment, amount):
        self.payment = payment
        self.amount = amount


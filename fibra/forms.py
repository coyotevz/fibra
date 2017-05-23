# -*- coding: utf-8 -*-

import locale
import decimal

from flask_wtf import Form
from wtforms import (
    widgets, TextField, TextAreaField, IntegerField, DecimalField, DateField,
    HiddenField, SubmitField
)
from wtforms.validators import Required, Optional, Length, NumberRange

from wtforms.ext.sqlalchemy.fields import (
        QuerySelectField, QuerySelectMultipleField
)

from fibra.models import Invoice

locale.setlocale(locale.LC_ALL, '')


class LocaleDecimalField(DecimalField):
    """Mimic DecimalField but support current locale number parsing."""

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = decimal.Decimal(str(locale.atof(valuelist[0])))
            except (decimal.InvalidOperation, ValueError):
                raise ValueError(self.gettext(u'Not a valid decimal value'))

    def _value(self):
        retval = super(LocaleDecimalField, self)._value()
        try:
            return retval.replace('.', locale.localeconv()['decimal_point'])
        except:
            return retval


class CustomerForm(Form):
    id = HiddenField()
    name = TextField('Nombre', validators=[Required()])
    address = TextField(u'Dirección')
    cuit = TextField('CUIT')
    notes = TextAreaField('Notas')


class ContactForm(Form):
    id = HiddenField()
    first_name = TextField('Nombre', validators=[Required()])
    last_name = TextField('Apellido')
    phone = TextField(u'Teléfono')
    mail = TextField(u'Correo Electrónico')
    role = TextField('Rol')
    notes = TextAreaField('Notas')


class CustomerInvoiceForm(Form):
    id = HiddenField()
    type = TextField(u'Tipo', validators=[Required(), Length(min=3, max=3)])
    point_sale = IntegerField(u'PV', validators=[Required(), NumberRange(min=1)])
    number = IntegerField(u'Número', validators=[Required(), NumberRange(min=1)])
    total = LocaleDecimalField(u'Total', validators=[Required(), NumberRange(min=0)])
    issue_date = DateField(u'Emisión', validators=[Required()], format="%d/%m/%Y")
    expiration_date = DateField(u'Vencimiento', validators=[Required()], format="%d/%m/%Y")
    notes = TextAreaField(u'Notas')


class InvoiceForm(CustomerInvoiceForm):
    customer = QuerySelectField('Cliente', get_label='name', allow_blank=True)


class InvoicePaymentForm(Form):
    date = DateField('Fecha de pago', validators=[Required()], format="%d/%m/%Y")
    receipt_number = IntegerField('Recibo', validators=[Optional()])
    amount = LocaleDecimalField('Monto', validators=[Required(), NumberRange(min=0)])
    notes = TextAreaField('Notas')


class CustomerPaymentForm(InvoicePaymentForm):
    invoices = QuerySelectMultipleField('Documentos a cancelar',
                    option_widget=widgets.CheckboxInput(),
                    get_label=lambda i: i.fulldesc)


class PaymentForm(CustomerPaymentForm):
    customer = QuerySelectField('Cliente', get_label='name', allow_blank=True)

    def validate(self):
        # 1. validate customer
        if self.customer.validate(self):
            customer = self.customer.data

            # 2. Build query for customer invoices
            self.invoices.query = Invoice.query.filter(Invoice.customer_id==customer.id)\
                                               .filter(Invoice.state.in_([u'PENDING', u'EXPIRED']))
            return super(PaymentForm, self).validate()
        return False

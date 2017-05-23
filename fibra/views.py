# -*- coding: utf-8 -*-

from datetime import date

from flask import render_template, redirect, url_for, flash, request, make_response
from werkzeug.urls import url_unquote

from fibra import app
from fibra.models import db, Customer, Contact, Invoice, Payment, STATES
from fibra.forms import (
        CustomerForm, ContactForm, InvoiceForm, CustomerInvoiceForm,
        PaymentForm, CustomerPaymentForm, InvoicePaymentForm
)
from fibra.report import GeneralReport, CustomerReport
from fibra.utils import render_json

@app.route("/")
def index():
    return redirect(url_for('customer_list'))


## Customers ##

@app.route('/customers/')
def customer_list():
    customers = Customer.query.join(Invoice)\
                    .filter(Invoice.state.in_([u'PENDING', u'EXPIRED']))\
                    .order_by(Invoice.expiration_date.asc())
    return render_template("customer_list.html", customers=customers)


@app.route('/customers/report/')
def customers_report():
    customers = Customer.query.join(Invoice)\
                    .filter(Invoice.state.in_([u'PENDING', u'EXPIRED']))\
                    .order_by(Invoice.expiration_date.asc())
    report = GeneralReport(query=customers)
    return report.response()


@app.route('/customers/<int:customer_id>/')
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    invoices = customer.invoices.order_by(Invoice.expiration_date.desc())
    return render_template("customer_detail.html", customer=customer, invoices=invoices)


@app.route('/customers/<int:customer_id>/report/')
def customer_report(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    report = CustomerReport(customer=customer)
    return report.response()


@app.route('/customers/<int:customer_id>/edit/', methods=['GET', 'POST'])
@app.route('/customers/new/', methods=['GET', 'POST'])
def customer_edit(customer_id=None):
    customer = Customer()
    msg = u"El nuevo cliente se creó satisfactoriamente"
    if customer_id:
        customer = Customer.query.get_or_404(customer_id)
        msg = u"El cliente se editó satisfactoriamente"
    if 'customer_name' in request.cookies and not customer.name:
        customer.name = url_unquote(request.cookies.get('customer_name'))
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        if not customer.id:
            customer.id = None
            db.session.add(customer)
        db.session.commit()
        flash(msg)
        resp = make_response(redirect(url_for('customer_detail', customer_id=customer.id)))
    else:
        if not form.id.data:
            form.id.data = None
        resp = make_response(render_template("customer_edit.html", form=form))
    resp.set_cookie("customer_name", '')
    return resp


@app.route('/customers/<int:customer_id>/invoices/new/', methods=['GET', 'POST'])
@app.route('/customers/<int:customer_id>/invoices/<int:invoice_id>/edit/', methods=['GET', 'POST'])
def customer_edit_invoice(customer_id, invoice_id=None):
    customer = Customer.query.get_or_404(customer_id)
    invoice = Invoice(issue_date=date.today())
    msg = u"El nuevo documento se agregó a <strong>%s</strong> satisfactoriamente" % customer.name
    if invoice_id:
        invoice = Invoice.query.get_or_404(invoice_id)
        msg = u"El documento se editó satisfactoriamente"
    form = CustomerInvoiceForm(obj=invoice)
    if form.validate_on_submit():
        form.populate_obj(invoice)
        if not invoice.id:
            invoice.id = None
            invoice.customer = customer
            db.session.add(invoice)
        db.session.commit()
        flash(msg)
        return redirect(url_for('customer_detail', customer_id=customer.id))
    if not form.id.data:
        form.id.data = None
    return render_template('invoice_edit.html', form=form, customer=customer)


@app.route('/customers/<int:customer_id>/pay/', methods=['GET', 'POST'])
def customer_add_payment(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerPaymentForm(date=date.today())
    form.invoices.query = search_invoices_query(customer_id=customer.id)
    if form.validate_on_submit():
        payment = Payment()
        invoices = form.invoices.data
        del form.invoices
        form.populate_obj(payment)
        payment.add_invoices(invoices)
        db.session.add(payment)
        db.session.commit()
        flash(u"El pago se agregó a <strong>%s</strong> satisfactoriamente" % customer.name)
        return redirect(url_for('customer_detail', customer_id=customer.id))
    return render_template("customer_add_payment.html", form=form, customer=customer)


## Contact ##

@app.route('/customers/<int:customer_id>/contacts/new/', methods=['GET', 'POST'])
@app.route('/customers/contacts/<int:contact_id>/edit/', methods=['GET', 'POST'])
def contact_edit(customer_id=None, contact_id=None):
    if customer_id:
        contact = Contact()
        customer = Customer.query.get_or_404(customer_id)
        msg = u"El contacto se agregó a <strong>%s</strong> satisfactoriamente" % customer.name
    if contact_id:
        contact = Contact.query.get_or_404(contact_id)
        customer = contact.customer
        msg = u"El contacto se editó satisfactoriamente"
    form = ContactForm(obj=contact)
    if form.validate_on_submit():
        form.populate_obj(contact)
        if not contact.id:
            contact.id = None
            contact.customer = customer
            db.session.add(contact)
        db.session.commit()
        flash(msg)
        return redirect(url_for("customer_detail", customer_id=customer.id))
    if not form.id.data:
        form.id.data = None
    return render_template("contact_edit.html", form=form, customer=customer)

## Invoices ##

@app.route('/customers/invoices/<int:invoice_id>/')
def invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("invoice_detail.html", invoice=invoice)


@app.route('/customers/invoices/new/', methods=['GET', 'POST'])
def invoice_new():
    invoice = Invoice(issue_date=date.today())
    form = InvoiceForm(obj=invoice)
    form.customer.query = Customer.query.order_by(Customer.name)
    if form.validate_on_submit():
        form.populate_obj(invoice)
        if not invoice.id:
            invoice.id = None
            db.session.add(invoice)
        db.session.commit()
        flash(u"El documento se agregó a <strong>%s</strong> satisfactoriamente" % form.customer.data.name)
        return redirect(url_for('customer_detail', customer_id=form.customer.data.id))
    return render_template('invoice_new.html', form=form)


@app.route('/customers/invoices/<int:invoice_id>/pay/', methods=['GET', 'POST'])
def invoice_add_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    form = InvoicePaymentForm(date=date.today(), amount=invoice.balance)
    if form.validate_on_submit():
        payment = Payment()
        form.populate_obj(payment)
        invoice.add_payment(payment)
        db.session.commit()
        flash(u"El pago se agregó a <strong>%s</strong> satisfactoriamente" % invoice.customer.name)
        return redirect(url_for('customer_detail', customer_id=invoice.customer.id))
    return render_template("invoice_add_payment.html", form=form, invoice=invoice)


## Payments ##

@app.route('/customers/invoices/pay/', methods=['GET', 'POST'])
def payment_new():
    form = PaymentForm(date=date.today())
    form.customer.query = Customer.query.filter(Customer.id==Invoice.customer_id)\
                                        .filter(Invoice.state.in_([u'PENDING', u'EXPIRED']))
    if form.validate_on_submit():
        payment = Payment()
        form.populate_obj(payment)
        db.session.add(payment)
        db.session.commit()
        flash(u"El pago se agregó a <strong>%s</strong> satisfactoriamente" % form.customer.data.name)
        return redirect(url_for('customer_list'))
    return render_template('payment_new.html', form=form)


# ajax interface

@app.route('/_search/customers/')
def ajax_search_customers():

    def _serialize(i):
        return {
            'value': i.name,
            'url': url_for('customer_detail', customer_id=i.id)
        }

    term = unicode(request.args.get('q', '', type=unicode)).strip().split()
    if term:
        query = Customer.query
        for t in term:
            query = query.filter(Customer.name.ilike('%'+t+'%'))
        customers = query.values('id', 'name')
        retval = map(_serialize, customers)
    else:
        retval = []
    return render_json(retval)


@app.route('/_search/invoices/')
def ajax_search_invoices():

    def _serialize(i):
        return {
            'id': i.id,
            'fulldesc': i.fulldesc,
            'state': i.state,
            'balance': str(i.balance),
            'expiration_date': i.expiration_date.isoformat(),
            'customer_id': i.customer_id,
        }

    customer_id = request.args.get('customer', None, type=int)
    states = request.args.getlist('state', type=str) or [u'PENDING', u'EXPIRED']

    query = search_invoices_query(customer_id, states)
    return render_json(map(_serialize, query))


# helpers
def search_invoices_query(customer_id=None, states=[u'PENDING', u'EXPIRED']):
    query = Invoice.query.order_by(Invoice.expiration_date.asc())
    if customer_id:
        query = query.join(Customer).filter(Customer.id==customer_id)
    if len(states) == 1 and states[0] in ("all", "*"):
        states = STATES.keys()
    return query.filter(Invoice.state.in_(states))

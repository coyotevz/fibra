#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decimal import Decimal

def dateformat_filter(date, format="%d %b, %Y"):
    if date:
        return date.strftime(format)
    return ''

_when = ["hoy", "ayer", "mañana"]

def timeago_filter(date):
    if date:
        today = date.today()
        days = (today - date).days

        if abs(days) < 2:
            return _when[days]

        if days < 0: # future
            msg = "en %s"
        elif days > 0:
            msg = "hace %s"
        else:
            return ''

        years, days = divmod(abs(days), 365)
        months, days = divmod(days, 30)
        chain = []
        if years:
            chain.append("%d año" % (years,) + ("s" if years > 1 else ""))
        if months:
            chain.append("%d mes" % (months,) + ("es" if months > 1 else ""))
        if days:
            chain.append("%d día" % (days,) + ("s" if days > 1 else ""))
        if len(chain) == 1:
            chain = "%s" % chain[0]
        else:
            chain = ", ".join(chain[:-1]) + " y " + chain[-1]
        return msg % chain
    return ''

def moneyfmt_filter(value, places=2, curr='', sep='.', dp=',',
                    pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formated string.

    places:     required number of places after the decimal point.
    curr:       optional currency symbol before the sign (may be blank)
    sep:        optional grouping separator (comma, period, space, or blank)
    dp:         decimal point indicator (comma or period)
    pos:        optional sign for positive numbers: '+', space or blank
    neg:        optional sign for negative numbers: '-', '(', space or blank
    trailneg:   optional trailing minus indicator: '-', ')', space or blank
    """
    q = Decimal(10) ** -places
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))

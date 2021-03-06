# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: name_
#
#
##############################################################################
#~ from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
import calendar
#~ import netsvc


##----------------------------------------------------- tcv_municipal_tax_print


__REPORT_TYPES__ = [
    ('tcv.municipal.tax.report', _("Municipal tax summary")),
    ('tcv.municipal.tax.products.report', _("Product's municipal tax")),
    ('tcv.municipal.tax.invoice.report', _("Municipal tax invoice detail"))]

__PERIODS__ = [
    ('year', _("Year")),
    ('0102', _("Bimonth 1 - Jan/Feb")),
    ('0304', _("Bimonth 2 - Mar/Apr")),
    ('0506', _("Bimonth 3 - May/Jun")),
    ('0708', _("Bimonth 4 - Jul/Ago")),
    ('0910', _("Bimonth 5 - Sep/Oct")),
    ('1112', _("Bimonth 6 - Nov/Dec"))]


class tcv_municipal_tax_print(osv.osv_memory):

    _name = 'tcv.municipal.tax.print'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'muni_tax_id': fields.many2one(
            'tcv.municipal.tax', 'Municipal tax',
            ondelete='restrict', required=True),
        'report_type': fields.selection(
            __REPORT_TYPES__, string='Report', required=True, readonly=False),
        'period': fields.selection(
            __PERIODS__, string='Period', required=True, readonly=False),
        }

    _defaults = {
        'report_type': lambda *a: 'tcv.municipal.tax.report',
        'period': lambda *a: 'year',
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_print_report(self, cr, uid, ids, context=None):
        context = context or {}
        for item in self.browse(cr, uid, ids, context={}):
            obj_tmt = self.pool.get('tcv.municipal.tax')
            data = obj_tmt.read(cr, uid, item.muni_tax_id.id)
            date = time.strptime(item.muni_tax_id.date_stop, '%Y-%m-%d')
            y = date.tm_year  # Year of data
            ld = calendar.monthrange(y, 2)[1]  # feb last day
            periods = {
                'year': {'date_start': '%s-01-01' % (y),
                         'date_stop': '%s-12-31' % (y)},
                '0102': {'date_start': '%s-01-01' % (y),
                         'date_stop': '%s-02-%s' % (y, ld)},
                '0304': {'date_start': '%s-03-01' % (y),
                         'date_stop': '%s-04-30' % (y)},
                '0506': {'date_start': '%s-05-01' % (y),
                         'date_stop': '%s-06-30' % (y)},
                '0708': {'date_start': '%s-07-01' % (y),
                         'date_stop': '%s-08-31' % (y)},
                '0910': {'date_start': '%s-09-01' % (y),
                         'date_stop': '%s-10-31' % (y)},
                '1112': {'date_start': '%s-11-01' % (y),
                         'date_stop': '%s-12-31' % (y)},
                }
            context.update(periods.get(item.period))
            context.update({
                'report_name': dict(__REPORT_TYPES__).get(item.report_type),
                'tax_period': item.period})
            if item.period == 'year':
                context.update({
                    'period_name': data.get('fiscalyear_id')[1]})
            else:
                context.update({
                    'period_name': dict(__PERIODS__).get(item.period, '')})
            datas = {
                'ids': [item.muni_tax_id.id],
                'model': 'tcv.municipal.tax',
                'form': data,
                }
            return {'type': 'ir.actions.report.xml',
                    'report_name': item.report_type,
                    'datas': datas,
                    'context': context}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_municipal_tax_print()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

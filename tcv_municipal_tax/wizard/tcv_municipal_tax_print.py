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
from report import report_sxw
from datetime import datetime
from osv import fields, osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time
import netsvc


##----------------------------------------------------- tcv_municipal_tax_print


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
        'report_type': fields.selection([
            ('tcv.municipal.tax.report',
             "Municipal tax summary"),
            ('tcv.municipal.tax.products.report',
             "Product's municipal tax"),
            ('tcv.municipal.tax.invoice.report',
             "Municipal tax invoice detail")],
            string='Report', required=True, readonly=False),
        }

    _defaults = {
        'report_type': lambda *a: 'tcv.municipal.tax.report',
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_print_report(self, cr, uid, ids, context=None):
        context = context or {}
        for item in self.browse(cr, uid, ids, context={}):
            obj_tmt = self.pool.get('tcv.municipal.tax')
            data = obj_tmt.read(cr, uid, item.muni_tax_id.id)
            datas = {
                'ids': [item.muni_tax_id.id],
                'model': 'tcv.municipal.tax',
                'form': data
                }
            return {'type': 'ir.actions.report.xml',
                    'report_name': item.report_type,
                    'datas': datas}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_municipal_tax_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-12-17
#    Version: 0.0.0.1
#
#    Description:
#    This wizard helps to create a supplies by product report
#
##############################################################################


#~ from report import report_sxw
#~ from tools.translate import _
from osv import fields, osv
import time
import datetime
#~ import tcv_mrp_gangsaw_summary
#~ import numpy as np

##------------------------------------------ tcv_mrp_blade_yield_wizard


class tcv_mrp_blade_yield_wizard(osv.osv_memory):

    _name = 'tcv.mrp.blade.yield.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_blade_yield_wizard, self).\
            default_get(cr, uid, fields, context)
        year = datetime.datetime.now().year
        data.update({'date_from': '%s-01-01' % year,
                     'date_to': time.strftime('%Y-%m-%d')})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Name', size=64, required=False, readonly=False),
        'date_from': fields.date('Date from', required=True),
        'date_to': fields.date('Date to', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True, ondelete='restrict'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_blade_yield_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

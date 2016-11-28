# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-12-17
#    Version: 0.0.0.1
#
#    Description:
#    This wizard helps to create a gangsaw summary report
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
import time
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import datetime
#~ import netsvc

##---------------------------------------------- tcv_mrp_gangsaw_summary_wizard


class tcv_mrp_gangsaw_summary_wizard(osv.osv_memory):

    _name = 'tcv.mrp.gangsaw.summary.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_gangsaw_summary_wizard, self).\
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
        'show_gs': fields.boolean('Show GS', help='Show Gangsaw summary'),
        'show_ps': fields.boolean('Show PS', help='Show Process summary'),
        'show_ms': fields.boolean('Show MS', help='Show Material summary'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'show_gs': lambda *a: True,
        'show_ps': lambda *a: True,
        'show_ms': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_summary_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

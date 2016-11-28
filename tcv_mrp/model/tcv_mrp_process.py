# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 03/10/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc

##------------------------------------------------------------- tcv_mrp_process


class tcv_mrp_process(osv.osv):

    _name = 'tcv.mrp.process'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=128, required=False, readonly=False,
            states={'open': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'open': [('readonly', False)]}),
        'ref': fields.char(
            'Reference', size=24, required=True, readonly=True),
        'state': fields.selection([(
            'open', 'Open'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'subprocess_ids': fields.one2many(
            'tcv.mrp.subprocess', 'process_id', 'Subprocess'),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'name': lambda *a: '',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'tcv.mrp.process', context=c),
        'state': lambda *a: 'open',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def update_name(self, cr, uid, ids, context=None):
        if not ids:
            return []
        ids = isinstance(ids, (int, long)) and [ids] or ids
        so_brw = self.browse(cr, uid, ids[0], context={})
        obj_tmp = self.pool.get('tcv.mrp.template')
        new_name = ''
        for sp in so_brw.subprocess_ids:
            ref_name = obj_tmp.get_var_value(cr, uid, sp.template_id.id,
                                             'ref_name') or ''
            if ref_name:
                new_name = '%s - %s' % (ref_name, sp. task_name)
                if new_name:
                    self.write(cr, uid, so_brw.id,
                               {'name': new_name}, context=context)
                    return True
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get
                        ('ir.sequence').get(cr, uid, 'tcv.mrp.process')})
        res = super(tcv_mrp_process, self).create(cr, uid, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        unlink_ids = []
        for pro in so_brw:
            if pro.state == 'open' and not pro.subprocess_ids:
                unlink_ids.append(pro['id'])
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete production process that are already ' +
                      'posted or have subprocess lines!'))
        res = super(tcv_mrp_process, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_mrp_process()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

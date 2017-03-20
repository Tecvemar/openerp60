# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2017-03-20
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc

##------------------------------------------------- tcv_mrp_production_supplies


class tcv_mrp_production_supplies(osv.osv):

    _name = 'tcv.mrp.production.supplies'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Ref', size=16, required=True, readonly=True),
        'name': fields.char(
            'Concept', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'narration': fields.text(
            'Notes', readonly=False),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=True, ondelete='restrict',
            help="The picking for this entry line"),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'user_id': lambda s, c, u, ctx: u,
        }

    _sql_constraints = [
        ('ref_uniq', 'UNIQUE(ref)', 'The ref must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').get(
                cr, uid, 'tcv.mrp.production.supplies')})
        res = super(tcv_mrp_production_supplies, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True

tcv_mrp_production_supplies()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

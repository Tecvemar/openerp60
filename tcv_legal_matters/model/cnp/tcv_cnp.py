# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-04-10
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

##------------------------------------------------------------------ tcv_cnp


class tcv_cnp(osv.osv):

    _name = 'tcv.cnp'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=False, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'line_ids': fields.one2many(
            'tcv.cnp.lines', 'cnp_id', 'Lines',
            readonly=True, states={'draft': [('readonly', False)]}),
        'narration': fields.text(
            'Notes', readonly=False),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

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

tcv_cnp()


##--------------------------------------------------------------- tcv_cnp_lines


class tcv_cnp_lines(osv.osv):

    _name = 'tcv.cnp.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            res.append((item.id, '%s' % (item.product_id.name)))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'sequence': fields.integer('Sequence'),
        'cnp_id': fields.many2one('tcv.cnp', 'C.N.P.', required=True,
                                  ondelete='cascade'),
        'hs_code_id': fields.many2one('tcv.sigesic.9901', 'HS Code',
                                      ondelete='restrict'),
        'part_no': fields.char('Part #', size=64),
        'name': fields.char('Name', size=64, required=False, readonly=False),
        'product_id': fields.many2one('product.product', 'Product',
                                      ondelete='restrict', required=True,
                                      help="Denominación o nombre " +
                                      "comercial del producto (Marca)"),
        'tech_specs': fields.related('product_id', 'tech_specs', type='text',
                                     string='Tech specs', store=False,
                                     readonly=True,
                                     help="Composición o características " +
                                     "físicas y/o químicas del producto"),
        'mark': fields.char('Mark', size=64, required=False, readonly=False),
        'qty': fields.float('Quantity', digits=(15, 2), readonly=False),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one',
                                 relation='product.uom', string='Uom',
                                 store=False, readonly=True),
        'unit_price': fields.float('Unit price', digits=(15, 2),
                                   readonly=False),
        'customs_facility_id': fields.many2one(
            'customs.facility', 'Customs Facility', change_default=True,
            ondelete='restrict'),
        'date_arrival': fields.date('Date arrival', select=True),
        'origin_country_id': fields.related(
            'product_id', 'origin_country_id', type='many2one',
            relation='res.country', string='Origin',
            store=False, readonly=True),
        'source_country_id': fields.many2one('res.country', 'Source country',
                                             ondelete='restrict'),

        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_hs_code_id(self, cr, uid, ids, hs_code_id, product_id):
        if product_id and hs_code_id:
            obj_prd = self.pool.get('product.product')
            prd = obj_prd.browse(cr, uid, product_id, context=None)
            if not prd.hs_code or hs_code_id != prd.hs_code:
                obj_hsc = self.pool.get('tcv.sigesic.9901')
                hsc = obj_hsc.browse(cr, uid, hs_code_id, context=None)
                obj_prd.write(cr, uid, prd.id, {'hs_code': hsc.code},
                              context=None)
        return {'value': {}}

    def on_change_product_id(self, cr, uid, ids, product_id):
        res = {}
        if product_id:
            obj_prd = self.pool.get('product.product')
            prd = obj_prd.browse(cr, uid, product_id, context=None)
            res.update({'tech_specs': prd.tech_specs,
                        'uom_id': prd.uom_id.id,
                        'origin_country_id': prd.origin_country_id.id,
                        'source_country_id': prd.origin_country_id.id,
                        'name': prd.name,
                        })
            if prd.hs_code:
                ids = self.pool.get('tcv.sigesic.9901').\
                    search(cr, uid, [('code', '=', prd.hs_code)])
                if ids and len(ids) == 1:
                    res.update({'hs_code_id': ids[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_cnp_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

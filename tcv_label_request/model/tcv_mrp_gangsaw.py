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

##------------------------------------------------------------- tcv_mrp_gangsaw


class tcv_mrp_gangsaw(osv.osv):

    _inherit = 'tcv.mrp.gangsaw'

    def button_done(self, cr, uid, ids, context=None):
        res = super(tcv_mrp_gangsaw, self).button_done(cr, uid, ids, context)
        obj_blk = self.pool.get('tcv.mrp.gangsaw.blocks')
        gangsaw = self.browse(cr, uid, ids, context=context)[0]
        for b in gangsaw.gangsaw_ids:
            if not b.label_id and not b.no_label:
                context.update({'gangsaw_note': gangsaw.parent_id.ref})
                obj_blk.create_label(cr, uid, ids, b, context)
        return res

    def test_draft(self, cr, uid, ids, *args):
        so_brw = self.browse(cr, uid, ids, context={})
        unlink_ids = []
        for g in so_brw:
            for b in g.gangsaw_ids:
                if b.label_id:
                    if b.label_id.state != 'draft':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t reset a process with proceced labels'))
                    else:
                        unlink_ids.append(b.label_id.id)
        if unlink_ids:
            self.pool.get('tcv.label.request').unlink(cr, uid, unlink_ids,
                                                      context={})
        return super(tcv_mrp_gangsaw, self).test_draft(cr, uid, ids, args)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw()


class tcv_mrp_gangsaw_blocks(osv.osv):

    _inherit = 'tcv.mrp.gangsaw.blocks'

    _columns = {
        'label_id': fields.many2one(
            'tcv.label.request', 'Labels', readonly=True, ondelete='set null'),
        'no_label': fields.boolean(
            'No label', required=True),
        }

    _defaults = {'no_label': False,
                 }

    _sql_constraints = [
        ('label_id_unique', 'UNIQUE(label_id)',
         'The label id must be unique!'),
        ]

    def create_label(self, cr, uid, ids, block, context=None):
        if not(block) or block.label_id:
            return False
        obj_lbl = self.pool.get('tcv.label.request')
        lot_name = block.prod_lot_id.name.split('-')
        if len(lot_name) == 1:
            lot_name = lot_name[0]
        else:
            lot_name = lot_name[1]
        lot_name = ('000000%s' % lot_name.strip())[-6:]
        label = {'date': time.strftime('%Y-%m-%d'),
                 'type': 'block',
                 'product_id': block.product_id.id,
                 'prod_lot_id': int(lot_name),
                 'quantity': block.slab_qty,
                 'note': block.gangsaw_id.parent_id.ref,
                 'user_id': uid,
                 'state': 'draft'}
        lbl_id = obj_lbl.create(cr, uid, label, context)
        self.write(cr, uid, [block.id], {'no_label': False,
                                         'label_id': lbl_id})
        return True

    def button_create_label(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for block in self.browse(cr, uid, ids, context={}):
            self.create_label(cr, uid, ids, block, context)
        return True

tcv_mrp_gangsaw_blocks()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

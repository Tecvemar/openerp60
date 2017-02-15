# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-26
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

from osv import osv

##------------------------------------------------------------------ stock_move


class stock_move(osv.osv):

    _inherit = 'stock.move'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

    def action_done(self, cr, uid, ids, context=None):
        '''
        Created to adjust stock_move.date to tcv_block_cost_lots.date_arrival
        '''
        res = super(stock_move, self).action_done(cr, uid, ids, context)
        for move in self.browse(cr, uid, ids, context={}):
            if move.product_id.stock_driver == 'block' and \
                move.location_id.location_id.name == 'Canteras' and \
                    move.location_dest_id.name == 'Patio bloques':
                obj_bcl = self.pool.get('tcv.block.cost.lots')
                block_ids = obj_bcl.search(cr, uid, [('prod_lot_id', '=',
                                                      move.prodlot_id.id)])
                if block_ids and len(block_ids) == 1:
                    block = obj_bcl.browse(cr, uid, block_ids[0], context)
                    self.write(cr, uid, move.id, {'date': block.date_arrival},
                               context)
        return res

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

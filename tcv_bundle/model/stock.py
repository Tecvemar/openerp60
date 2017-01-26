# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#~ ###########################################################################

from osv import fields, osv
import decimal_precision as dp
import time
#~ from tools.translate import _


##-------------------------------------------------------- stock_production_lot


class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _fnct_get_bundle_id(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        tbl_obj = self.pool.get('tcv.bundle.lines')
        tbl_ids = tbl_obj.search(
            cr, uid, [('prod_lot_id','in',ids)], context=context)
        tbl_brws = tbl_obj.browse(cr, uid, tbl_ids, context=context)
        res = {}.fromkeys(ids,False)
        for i in tbl_brws:
            res[i.prod_lot_id.id] = i.bundle_id.id or False
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'bundle_id': fields.function(_fnct_get_bundle_id, method=True,
            type='many2one', relation='tcv.bundle',
            string='Bundle'),
        }

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

stock_production_lot()

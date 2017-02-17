
# -*- coding: utf-8 -*-
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
##############################################################################
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
import netsvc   



class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def action_move_create(self, cr, uid, ids, *args):
        '''
        Validate invoices and generating picking 
        '''
        res = super(account_invoice, self).action_move_create(cr, uid, ids, ())
        invoice_brw = self.browse(cr,uid,ids[0],context={})
        sale_obj = self.pool.get('sale.order')
        for i in invoice_brw.invoice_line:
            if i.prod_lot_id.stock_move_id and invoice_brw.type == 'out_invoice':
                sale_obj.create_internal_sale(cr,uid,ids,invoice_brw,i,context={})
            else:
                pass
        return res
account_invoice()

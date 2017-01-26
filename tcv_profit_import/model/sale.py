# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields

#
# Model definition
#
class sale_order(osv.osv):
    
    _inherit = 'sale.order'

    _columns = {
        'profit_doc':fields.integer('Profit document #'),
        'profit_inv':fields.integer('Profit invoice #'),
        'profit_db':fields.many2one('tcv.profit.import.config', 'Profit DB', ondelete='set null'),
    }

    _defaults = {
        'profit_doc': 0,
    }
    
    
    #~ def _make_invoice(self, cr, uid, order, lines, context=None):
        #~ print '_make_invoice'
        #~ inv_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        #~ inv = context.get('invoice_profit_data')
        #~ print inv['nro_ctrl']
        #~ inv_data = {'nro_ctrl':inv['nro_ctrl'],
                    #~ 'payment_term':4
                    #~ }
        #~ self.pool.get('account.invoice').write(cr, uid, inv_id, inv_data, context)
        #~ return inv_id
        
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

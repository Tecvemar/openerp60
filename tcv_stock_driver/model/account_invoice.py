
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


class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    _columns = {
                'prod_lot_id':fields.many2one('stock.production.lot','Production lot',ondelete='restrict'),
                'pieces':fields.integer('Pieces',require=True),
                'quantity':fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
                }
account_invoice_line()


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    _columns = {
        'special':fields.boolean('Special',digits_compute=dp.get_precision('Invoices generated in procces intercompany')),
                }
    _defaults = {
        'special':False,
    }

    def _refund_cleanup_lines(self, cr, uid, lines):
        """ Initializes the fields of the lines of a refund invoice
        prod_lot_id
        """
        data = super(account_invoice, self)._refund_cleanup_lines(
            cr, uid, lines)
        list = []
        for x, y, res in data:
            if res.get('prod_lot_id'):
                res.update({'prod_lot_id': res['prod_lot_id'][0]})
            list.append((x, y, res))
        return list

    #~ def _refund_cleanup_lines(self, cr, uid, lines):
        #~ """
        #~ Metodo creado para agregar ,"prod_lot_id" en la generacion de la factura rectificativa
        #~ """
        #~ for line in lines:
            #~ del line['id']
            #~ del line['invoice_id']
            #~ #TODO Verify one more elegant way to do this
            #~ for field in ('company_id', 'partner_id', 'account_id', 'product_id',
                          #~ 'uos_id', 'account_analytic_id', 'tax_code_id', 'base_code_id',
                          #~ 'prod_lot_id', 'concept_id', 'tax_id', 'wh_xml_id'):
                #~ line[field] = line.get(field, False) and line[field][0]
            #~ if 'invoice_line_tax_id' in line:
                #~ line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
        #~ return map(lambda x: (0,0,x), lines)

account_invoice()

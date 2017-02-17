# -*- encoding: utf-8 -*-
##############################################################################
#
#~ Incorpora el campo para asociar la linea de la factura con su comisión
#~ correspondiente
#
##############################################################################
from osv import fields, osv


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def _refund_cleanup_lines(self, cr, uid, lines):
        #~ Clear any reference to tcv_sale_commission_id on refund
        map(lambda d: d.pop('tcv_sale_commission_id'), lines)
        res = super(account_invoice, self)._refund_cleanup_lines(
            cr, uid, lines)
        return res

account_invoice()


class account_invoice_line(osv.osv):

    _inherit = "account.invoice.line"

    _columns = {
        'tcv_sale_commission_id': fields.many2one(
            'tcv.sale.commission.line', 'Invoice Lines',
            readonly=True, ondelete='set null'),
        }

account_invoice_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

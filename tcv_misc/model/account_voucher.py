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

#~ import time
#~ from lxml import etree

#~ import netsvc
from osv import osv, fields
#~ import decimal_precision as dp
#~ from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    def proforma_voucher(self, cr, uid, ids, context=None):
        ## added to clean unnecesary lines in account.voucher.lines (amount == 0
        res = super(account_voucher, self).proforma_voucher(cr, uid, ids, context)
        unlink_ids = []
        for v in self.browse(cr,uid,ids,context=context):
            for l in v.line_ids:
                if not l.amount:
                    unlink_ids.append(l.id)
        if unlink_ids:
            self.pool.get('account.voucher.line').unlink(cr,uid,unlink_ids)
        return res

account_voucher()

class account_voucher_line(osv.osv):
    _inherit = 'account.voucher.line'

    _columns = {
        'move_line_id': fields.many2one('account.move.line', 'Journal Item',ondelete='restrict'),
    }

account_voucher_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

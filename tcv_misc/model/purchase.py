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
from tools.translate import _
import pooler

#~ Moved to tcv_Purchase


#
# Model definition
#
#~ class purchase_order(osv.osv):
#~ 
    #~ _inherit = "purchase.order"
#~ 
    #~ def onchange_partner_id(self, cr, uid, ids, part):
        #~ ### Added to set the default purchase location (purchase dest) from partner fields
        #~ res = super(purchase_order, self).onchange_partner_id(cr, uid, ids, part )
        #~ if part:
            #~ obj_pnr = self.pool.get('res.partner')
            #~ partner = obj_pnr.browse(cr,uid,part,context=None)
            #~ if partner.property_stock_purchase:
                #~ location_id = partner.property_stock_purchase.id
                #~ res['value'].update({'location_id':location_id})
        #~ return res
#~ 
#~ purchase_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

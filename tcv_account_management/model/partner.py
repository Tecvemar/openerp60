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
##############################################################################

#~ Se sobreescribe para transmitir el ID del partner via context
#~ Requiere solucion bug:
#~      https://bugs.launchpad.net/account-management/+bug/994168
#~ Los datos se transfireren en el key:res_partner_account_id_ref

from osv import fields, osv


class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'property_account_advance': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Advance",
            method=True,
            view_load=True,
            domain="[('type', '=', 'payable')]",
            help="This account will be used instead of the default one " +
            "as the advance account for the current partner",
            required=False,
            readonly=False),
        'property_account_prepaid': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Prepaid",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="This account will be used instead of the default one as " +
            "the prepaid account for the current partner",
            required=False,
            readonly=False),
        }

    def _gen_property_account(self, cr, uid, ids, vals, field, account_kind,
                              context=None):
        if not vals.get(account_kind):
            return {}
        partner = self.browse(cr, uid, ids)[0]
        rpa_obj = self.pool.get('res.partner.account')
        rpa = rpa_obj.browse(cr, uid, vals[account_kind])
        if not rpa.use_advance:
            return {field: rpa.property_account_advance_default.id}
        elif account_kind == 'account_kind_rec':
            if not(vals.get('customer') and vals.get('account_kind_rec')):
                return {field: rpa.property_account_advance_default.id}
        elif account_kind == 'account_kind_pay':
            if not(vals.get('supplier') and vals.get('account_kind_pay')):
                return {field: rpa.property_account_advance_default.id}
        aa_obj = self.pool.get('account.account')
        code = '%s%00005d' % (rpa.property_parent_advance.code,
                              partner.id)
        account_id = aa_obj.search(cr, uid, [('code', '=', code)])
        if not account_id:
            account_name = partner.name
            parent_name = rpa.property_parent_advance.name

            user = self.pool.get('res.users').browse(cr, uid, uid,
                                                     context=context)
            new_account = {
                #~ 'name': 'CXC %s' % (partner['name']),
                'code': code,
                'name': u'%s - %s' % (parent_name, account_name),
                'parent_id': rpa.property_parent_advance.id,
                'company_id': user.company_id.id,
                'type': rpa.property_account_advance_default.type,
                'user_type': rpa.user_type_advance.id,
                'reconcile': True,
                'auto': False,
                'active': True,
                'currency_mode': 'current',
                }
            account_id = aa_obj.create(cr, uid, new_account, context)
        else:
            account_id = account_id and account_id[0]
        return {field: account_id}

    def create(self, cr, uid, vals, context=None):
        """
        Avoid to create a partner's account before optain partners id
        -- Use default property account meanwhile --
        """
        write_vals = {}
        #~ save_vals = {}
        #~ save_vals.update(vals)
        property_keys = {'account_kind_pay':
                         [('property_account_payable',
                           'property_account_partner_default'),
                          ('property_account_advance',
                           'property_account_advance_default')
                          ],
                         'account_kind_rec':
                         [('property_account_receivable',
                           'property_account_partner_default'),
                          ('property_account_prepaid',
                           'property_account_advance_default')
                          ],
                         }
        for key in property_keys.keys():
            if vals.get(key):
                obj_rpa = self.pool.get('res.partner.account')
                rpa_brw = obj_rpa.browse(cr, uid, vals[key], context=context)
                for prop in property_keys[key]:
                    vals.update({
                        prop[0]: rpa_brw[prop[1]].id})
                write_vals.update({key: vals.pop(key)})
        id = super(res_partner, self).create(cr, uid, vals, context)
        if write_vals:
            self.write(cr, uid, id, write_vals, context=context)
        return id

    def write(self, cr, uid, ids, vals, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for id in ids:
            #  Allways send customer & account_kind_rec and
            #  supplier & account_kind_pay
            pnr = self.browse(cr, uid, id, context=context)
            if 'customer' in vals or 'account_kind_rec' in vals:
                vals.update({
                    'customer': vals.get('customer', pnr.customer),
                    'account_kind_rec': vals.get('account_kind_rec',
                                                 (pnr.account_kind_rec and
                                                  pnr.account_kind_rec.id)),
                    })
                vals.update(
                    self._gen_property_account(
                        cr, uid, [id], vals,
                        'property_account_advance',
                        'account_kind_rec', context=None))
            if 'supplier' in vals or 'account_kind_pay' in vals:
                vals.update({
                    'supplier': vals.get('supplier', pnr.supplier),
                    'account_kind_pay': vals.get('account_kind_pay',
                                                 (pnr.account_kind_pay and
                                                  pnr.account_kind_pay.id)),
                    })
                vals.update(
                    self._gen_property_account(
                        cr, uid, [id], vals,
                        'property_account_prepaid',
                        'account_kind_pay', context=None))
        res = super(res_partner, self).write(cr, uid, ids, vals, context)
        return res

    def _update_code(self, cr, uid, ids, vals, context=None):
        context.update({'res_partner_account_id_ref': ids})
        return super(res_partner, self).\
            _update_code(cr, uid, ids, vals, context)

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

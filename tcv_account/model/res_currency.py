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
#~ ############################################################################
from osv import fields, osv
#~ import decimal_precision as dp
#~ from tools.translate import _
import time

#~ Se redefine el modelo res_currency_rate para incluir el campo inv_rate que
#~ permite mostrar la tasa con un valor más normal
#~      1 USD = inv_rate VEB -> rate = 1/inv_rate
#~      rate USD = 1/4,3  = 0.232558  ->  rate = 0.232558, inv_rate = 4.30


class res_currency(osv.osv):

    _inherit = "res.currency"

    def _current_inv_rate(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        if 'date' in context:
            date = context['date']
        else:
            date = time.strftime('%Y-%m-%d')
        date = date or time.strftime('%Y-%m-%d')
        for id in ids:
            cr.execute("SELECT currency_id, inv_rate FROM res_currency_rate " +
                       "WHERE currency_id = %s AND name <= %s " +
                       "ORDER BY name desc LIMIT 1", (id, date))
            if cr.rowcount:
                id, irate = cr.fetchall()[0]
                res[id] = irate
            else:
                res[id] = 0
        return res

    _columns = {
        'inv_rate': fields.function(
            _current_inv_rate, method=True, string='Current Inv. Rate',
            digits=(12, 6), help='The inverse rate of the currency to the ' +
            'currency of rate 1 (rate = 1/inv_rate)'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict',
            help="Account for rounding diff currency related issues"),
        }

res_currency()


class res_currency_rate(osv.osv):

    _inherit = "res.currency.rate"

    _columns = {
        'rate': fields.float(
            'Rate', digits=(20, 12), required=True,
            help='The rate of the currency to the currency of rate 1'),
        'inv_rate': fields.float(
            'Inv. rate', digits=(20, 12),
            help='The inverse rate of the currency to the currency of ' +
            'rate 1 (rate = 1/inv_rate)'),
        }

    def on_change_compute_rate(self, cr, uid, ids, inv_rate):
        res = {}
        if inv_rate != 0:
            res = {'value': {'rate': 1 / inv_rate}}
        return res

res_currency_rate()

# -*- encoding: utf-8 -*-
###############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-07-22
#    Version: 1.0
#
#    Description:
#
#
###############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##---------------------------------------------------------- tcv_internal_forms


class tcv_internal_forms(osv.osv):

    _name = 'tcv.internal.forms'

    _description = ''

    _order = 'ref'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Reference', size=16, required=True, readonly=False),
        'name': fields.char(
            'Name', size=128, required=True, readonly=False),
        'date': fields.date(
            'Date', required=True, readonly=False, select=True),
        'revision': fields.float(
            'Revision', digits_compute=dp.get_precision('Account'),
            required=True),
        'narration': fields.text(
            'Text', readonly=False),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'group_id': fields.many2one(
            'tcv.internal.forms.group', 'Group', required=False,
            ondelete='restrict'),
        'personal_ids': fields.one2many(
            'tcv.internal.forms.personal', 'personal_id', 'Personal'),
        'active': fields.boolean(
            'Active', required=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'revision': lambda *a: 1,
        'active': lambda *a: True,

        }

    _sql_constraints = [
        ('ref_uniq', 'UNIQUE(ref)', 'The ref must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_internal_forms()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

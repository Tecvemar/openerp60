# -*- coding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 13/09/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################

#~ TODO: Agregar validacion para que todos los servicios asociados pertenezcan
#~ a la cuenta 62401

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------- account_invoice


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    _columns = {
        'import_id': fields.many2one(
            'tcv.import.management', 'Import exp', required=False,
            ondelete='restrict', domain=[('state', '=', 'open')]),
        'cost_applied': fields.boolean(
            'Cost applied', required=True, readonly=False,
            help="Indicate if a cost of goods was applied to import. " +
            "Only apply for import"),
        }

    _defaults = {
        'cost_applied': lambda *a: False,
        }

    def test_open(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.type == 'in_invoice':
                cfg = self.pool.get('tcv.import.management').\
                    get_import_config(cr, uid)
                if item.journal_id.id == cfg.journal_id.id and \
                        not item.import_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must indicate an Import expedient if ' +
                          'journal = "%s"') % cfg.journal_id.name)
                elif item.journal_id.id != cfg.journal_id.id and \
                        item.import_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can\'t indicate an Import expedient if ' +
                          'journal <> "%s"') % cfg.journal_id.name)
        if hasattr(super(account_invoice, self), "test_open"):
            return super(account_invoice, self).test_open(cr, uid, ids, args)
        else:
            return True

    def on_change_import_id(self, cr, uid, ids, import_id):
        res = {}
        if import_id:
            obj_imp = self.pool.get('tcv.import.management')
            cfg = obj_imp.get_import_config(cr, uid)
            res = {'value': {'journal_id': cfg.journal_id.id}}
        else:
            res = {'value': {'expedient': False}}
        return res

account_invoice()

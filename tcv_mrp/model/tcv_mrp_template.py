# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 03/10/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------ tcv_mrp_template


class tcv_mrp_template(osv.osv):

    _name = 'tcv.mrp.template'

    _description = ''

    _order = 'sequence'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=32, required=True, readonly=False),
        'res_model': fields.many2one(
            'ir.model', 'Model', required=True, ondelete='restrict',
            domain=[('model', 'ilike', 'tcv.mrp.')],
            help="Main object to handle task"),
        'input_model': fields.many2one(
            'ir.model', 'Input', required=False, ondelete='restrict',
            domain=[('model', 'ilike', 'tcv.mrp.io.')],
            help="Input data object to task"),
        'output_model': fields.many2one(
            'ir.model', 'Output', required=False, ondelete='restrict',
            domain=[('model', 'ilike', 'tcv.mrp.io.')],
            help="Output data object from task"),
        'param_ids': fields.one2many(
            'tcv.mrp.template.param', 'param_id', 'Parameters'),
        'journal_id': fields.many2one(
            'account.journal', 'Account journal', required=True,
            ondelete='restrict'),
        'stock_journal_id': fields.many2one(
            'stock.journal', 'Stock journal', required=True,
            ondelete='restrict'),
        'sequence': fields.integer(
            'Sequence'),

        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def get_var_value(self, cr, uid, template_id, var_code, context=None):
        obj_tmp = self.pool.get('tcv.mrp.template')
        template = obj_tmp.browse(cr, uid, template_id, context)
        for value in template.param_ids:
            if value.name == var_code:
                if value.type == 'char':
                    return value.char_val
                elif value.type == 'float':
                    return value.float_val
                elif value.type == 'bool':
                    return value.bool_val
                elif value.type == 'account':
                    if not value.account_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Must indicate %s value in template') %
                            value.name)
                    return value.account_id.id
        return False

    def get_all_values(self, cr, uid, template_id, context=None):
        obj_tmp = self.pool.get('tcv.mrp.template')
        template = obj_tmp.browse(cr, uid, template_id, context)
        res = {}
        for value in template.param_ids:
            if value.type == 'char':
                res.update({value.name: value.char_val})
            elif value.type == 'float':
                res.update({value.name: value.float_val})
            elif value.type == 'bool':
                res.update({value.name: value.bool_val})
            elif value.type == 'account':
                if not value.account_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must indicate %s value in template') % value.name)
                res.update({value.name: value.account_id.id})
        return res

    def load_parameters(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        for tmp in so_brw:
            obj_tsk = self.pool.get(tmp.res_model.model)
            params = obj_tsk._template_params()
            #~ params.extend()
            for p in tmp.param_ids:
                for x in params:
                    if x['name'] == p.name:
                        params.pop(params.index(x))
            if params:
                lines = []
                for x in params:
                    lines.append((0, 0, x))
                self.write(cr, uid, tmp.id, {'param_ids': lines}, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_template()


##-------------------------------------------------------- tcv_mrp_template_var

class tcv_mrp_template_param(osv.osv):

    _name = 'tcv.mrp.template.param'

    _description = ''

    _order = 'sequence,name'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    def _show_param_value(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        for item in self.browse(cr, uid, ids, context={}):
            if item.type == 'char':
                res[item.id] = item.char_val
            elif item.type == 'float':
                res[item.id] = '%.4f' % item.float_val
            elif item.type == 'bool':
                res[item.id] = _('True') if item.bool_val else _('False')
            elif item.type == 'account':
                res[item.id] = '%s %s' % (item.account_id.code,
                                          item.account_id.name)
            else:
                res[item.id] = 'type error'
        return res

    _columns = {
        'param_id': fields.many2one(
            'tcv.mrp.template', 'Template', required=True, ondelete='cascade'),
        'sequence': fields.integer(
            'Sequence'),
        'name': fields.char(
            'Name', size=32, required=True, readonly=False),
        'type': fields.selection(
            [('char', 'String'),
             ('float', 'Number'),
             ('bool', 'Boolean'),
             ('account', 'Acount')],
            string='Type', required=True, readonly=False),
        'char_val': fields.char(
            'String', size=64),
        'float_val': fields.float(
            'Number', digits=(16, 4)),
        'bool_val': fields.boolean(
            'Boolean'),
        'account_id': fields.many2one(
            'account.account', 'Account', readonly=False, ondelete='restrict',
            domain=[('type', '!=', 'view')]),
        'help': fields.char(
            'Help', size=96, readonly=True),
        'value': fields.function(
            _show_param_value, method=True, type='char', size=32,
            string='Value'),
        }

    _defaults = {
        'type': lambda *a: 'char',
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(param_id,name)', 'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    def on_change_value(self, cr, uid, ids, type, char_val, float_val,
                        bool_val, account_id):
        if not type:
            return {}
        if type == 'char':
            value = {'value': char_val}
        elif type == 'float':
            value = {'value': '%.4f' % float_val}
        elif type == 'bool_val':
            value = {'value': _('True') if bool_val else _('False')}
        elif type == 'account':
            name = ''
            if account_id:
                value = self.pool.get('account.account').\
                    browse(cr, uid, account_id, context=None)
                name = '%s %s' % (value.code, value.name)
            value = {'value': name}
        return {'value': value}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_template_param()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

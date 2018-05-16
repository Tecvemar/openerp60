# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-04-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# ~ from datetime import datetime
from osv import fields, osv
# ~ from tools.translate import _
# ~ import pooler
# ~ import decimal_precision as dp
# ~ import time
# ~ import netsvc

##------------------------------------------------------------ tcv_reconvertion


class tcv_reconvertion(osv.osv):

    _name = 'tcv.reconvertion'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'date': fields.date(
            'Date', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'models_ids': fields.one2many(
            'tcv.reconvertion.models', 'line_id', 'Models'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def find_table_and_field(self, cr, uid, model_name, column_name=None):
        params = {
            'table_name': model_name.replace('.', '_'),
            'column_name': column_name,
            }
        if not column_name:
            sql = """
            select * from information_schema.tables
            where table_name=%(table_name)s and
                  table_type != 'VIEW' limit 1
            """
        else:
            sql = """
            select * from information_schema.columns
            where table_name=%(table_name)s AND
                  column_name = %(column_name)s limit 1"""
        cr.execute(sql, params)
        res = cr.fetchall()
        return res

    ##-------------------------------------------------------- buttons (object)

    def button_load(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.models_ids:
                return True
        obj_ir_model = self.pool.get('ir.model')
        obj_models = self.pool.get('tcv.reconvertion.models')
        obj_rule = self.pool.get('ir.rule')
        models_ids = obj_ir_model.search(cr, uid, [])
        sec = 0
        for irmodel in obj_ir_model.browse(cr, uid, models_ids, context=None):
            # Check if model have data
            obj = self.pool.get(irmodel.model)
            if obj and self.find_table_and_field(cr, uid, irmodel.model):
                # Look for float fields stored in db
                stored = obj.search(cr, 1, [], limit=1)
                float_fields = [
                    fld for fld in irmodel.field_id if fld.ttype == 'float']
                fields_data = {}
                for field_name, field in obj._columns.items():
                    if field_name in [fld.name for fld in float_fields]:
                        store = type(field).__name__ != 'function' or (
                            type(field).__name__ == 'function' \
                            and field.store)
                        fields_data.update({
                            field_name: {
                                'fld_type': type(field).__name__,
                                'store': store,
                                }
                            })

                if stored and float_fields:
                    use_company_rule = obj_rule.search(
                        cr, uid, [('model_id', '=', irmodel.id),
                                  ('domain_force', 'ilike', '%company%')])
                    sec += 100
                    data = {
                        'line_id': ids[0],
                        'model_id': irmodel.id,
                        'sequence': sec,
                        'use_company_rule': use_company_rule,
                        'fields_ids': [(0, 0, {
                            'field_id': fld.id,
                            'fld_type': fields_data[fld.name]['fld_type'],
                            'store': fields_data[fld.name]['store'],
                            }) for fld in float_fields],
                        }
                    # Check if at least 1 field is stored in db
                    stored_data = [x[2]['store'] for x in data['fields_ids']]
                    if [value for value in stored_data if value]:
                        obj_models.create(cr, uid, data, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_reconvertion()


##----------------------------------------------------- tcv_reconvertion_models


class tcv_reconvertion_models(osv.osv):

    _name = 'tcv.reconvertion.models'

    _description = ''

    _order = 'sequence'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.reconvertion', 'Reconvertion', required=True,
            ondelete='cascade'),
        'model_id': fields.many2one(
            'ir.model', 'Model', required=True, ondelete='restrict',
            help="Model with data to be reconvtypeertered"),
        'model_name': fields.related(
            'model_id', 'model', type='char', size=32,
            string='Label', store=False, readonly=True),
        'status': fields.selection(
            [('draft', 'Draft'),
             ('toreconvert', 'To Reconvert'),
             ('ignore', 'Ignore (No reconvert)'),
             ('done', 'Done')],
            string='Status', required=True, readonly=False),
        'fields_ids': fields.one2many(
            'tcv.reconvertion.fields', 'model_id', 'Fields'),
        'sequence': fields.integer(
            'Sequence'),
        'use_company_rule': fields.boolean(
            'Compny rule'),
        }

    _defaults = {
        'status': lambda *a: 'draft',
        'use_company_rule': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_reconvertion_models()


##----------------------------------------------------- tcv_reconvertion_fields


class tcv_reconvertion_fields(osv.osv):

    _name = 'tcv.reconvertion.fields'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'model_id': fields.many2one(
            'tcv.reconvertion.models', 'Model', required=True,
            ondelete='cascade'),
        'field_id': fields.many2one(
            'ir.model.fields', 'Field', required=True, ondelete='restrict',
            help="Field with data to be reconvertered",
            domain="[('model_id', '=', parent.model_id)," +
                   " ('ttype', '=', 'float')]"),
        'name': fields.related(
            'field_id', 'name', type='char', size=256,
            string='Name', store=False, readonly=True),
        'fld_type': fields.char(
            'Field type', size=16, required=False, readonly=True),
        'method': fields.selection(
            [('account', 'Account'),
             ('normal', 'Normal'),
             ('property', 'Property Field'),
             ('noreconvert', 'No reconvert')],
            string='Method', required=True, readonly=False),
        'rounding': fields.selection(
            [('0.01', '0.01'),
             ('0.5', '0.5'),
             ('0.00001', '0.00001'),
             ('none', 'None')],
            string='Rounding', required=True, readonly=False),
        'store': fields.boolean(
            'Stored'),
        }

    _defaults = {
        'method': lambda *a: 'noreconvert',
        'rounding': lambda *a: '0.00001',
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    def on_change_field_id(self, cr, uid, ids, field_id):
        res = {}
        if field_id:
            obj_fld = self.pool.get('ir.model.fields')
            fld_brw = obj_fld.browse(cr, uid, field_id, context=None)
            res.update({'name': fld_brw and fld_brw.name or ''})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_reconvertion_fields()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

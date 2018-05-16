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
            where table_name=%(table_name)s limit 1
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
        models_ids = obj_ir_model.search(cr, uid, [('model', 'ilike', 'stock')])
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
                        fields_data.update({
                            field_name: {
                                'fld_type': type(field).__name__,
                                }
                            })

                if stored and float_fields:
                    sec += 100
                    data = {
                        'line_id': ids[0],
                        'ir_model': irmodel.id,
                        'sequence': sec,
                        'fields_ids': [(0, 0, {
                            'field_id': fld.id,
                            'fld_type': fields_data[fld.name]['fld_type']
                            }) for fld in float_fields],
                        }
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
        'ir_model': fields.many2one(
            'ir.model', 'Model', required=True, ondelete='restrict',
            help="Model with data to be reconvtypeertered"),
        'model_name': fields.related(
            'ir_model', 'model', type='char', size=32,
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
        }

    _defaults = {
        'status': lambda *a: 'draft',
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
            domain="[('model_id', '=', parent.ir_model)," +
                   " ('ttype', '=', 'float')]"),
        'name': fields.related(
            'field_id', 'name', type='char', size=256,
            string='Name', store=False, readonly=True),
        'fld_type': fields.char(
            'Field type', size=16, required=False, readonly=True),
        'type': fields.selection(
            [('account', 'Account'),
             ('normal', 'Normal'),
             ('property', 'Property Field'),
             ('noreconvert', 'No reconvert')],
            string='type', required=True, readonly=False),
        'rounding': fields.selection(
            [('0.01', '0.01'),
             ('0.5', '0.5'),
             ('0.00001', '0.00001'),
             ('none', 'None')],
            string='Rounding', required=True, readonly=False),
        }

    _defaults = {
        'type': lambda *a: 'normal',
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

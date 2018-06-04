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
    """
    Stores main data for reconverton proces (l10n_ve)
    """

    _name = 'tcv.reconvertion'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _create_sql_test(self, cr, uid, model, fields, context=None):
        norm_flds = [f.field_id.name for f in fields
                     if f.method == 'normal' and f.store and
                     f.fld_type != 'property']
        rev_flds = [f.field_id.name for f in fields
                    if f.method == 'reverse' and f.store and
                    f.fld_type != 'property']
        tables = ['%s mdl' % (model.model_id.model.replace('.', '_'))]
        sql_com = model.line_id.sql_command
        base_sql = 'mdl.%(f)s, ' + '%s.%s' % ('mdl', sql_com % '%(f)s') + \
                   ' as %(f)s_r'
        norm_flds_sel = [base_sql % {'f': f} for f in norm_flds]

        sql_rev = model.line_id.sql_reverse
        base_sql_rev = 'mdl.%(f)s, ' + '%s.%s' % ('mdl', sql_rev % '%(f)s') + \
                       ' as %(f)s_r'
        norm_flds_sel.extend([base_sql_rev % {'f': f} for f in rev_flds])
        prop_flds = [f.field_id.name for f in fields
                     if f.method == 'normal' and f.store and
                     f.fld_type == 'property']
        p = 0
        for f in prop_flds:
            p += 1
            p_idx = 'p%02d' % p
            res_id = "'%s,' || cast(mdl.id as varchar)" % (
                model.model_id.model)
            prop_tbl = "left join ir_property %s on %s.name = '%s' and " \
                       "%s.company_id = %s and " \
                       "%s.res_id = %s" % (
                           p_idx, p_idx, f,
                           p_idx, model.line_id.company_id.id,
                           p_idx, res_id)

            tables.append(prop_tbl)
            ffldn = '%s.%s' % (p_idx, 'value_float')
            norm_flds_sel.append(
                u'%s as %s, %s as %s_r' % (
                    ffldn, f, sql_com % ffldn, f))
        model_name = model.model_id.model.replace('.', '_')
        sql = (u'-- %s %s' % (model_name, '-' * 60))[:64] + '\n' + \
            u'select \n\t' + \
            u', \n\t'.join(norm_flds_sel) + '\n' +\
            u'from ' + \
            u'\n'.join(tables)
        where = []
        if model.use_company_rule:
            where.append(u'mdl.company_id=%s' % (
                model.line_id.company_id.id))
        if model.where:
            where.append(model.where)
        if where:
            sql += u'\nwhere ' + u' and '.join(where)
        sql += u'\nlimit 100;\n\n'
        return sql

    def _create_sql_reconvert(self, cr, uid, model, fields, context=None):
        flds = [f.field_id.name for f in fields
                if f.method == 'normal' and f.store and
                f.fld_type != 'property']
        sql_com = model.line_id.sql_command
        table = model.model_id.model.replace('.', '_')

        update_flds = ['%s = ' % f + sql_com % '%(f)s' % {'f': f}
                       for f in flds]
        model_name = model.model_id.model.replace('.', '_')
        sql = (u'-- %s%s' % (model_name, '-' * 60))[:64] + '\n' + \
            u'update %s mdl set\n\t' % table + \
            u', \n\t'.join(update_flds) + '\n'
        where = []
        if model.use_company_rule:
            where.append(u'mdl.company_id=%s' % (
                model.line_id.company_id.id))
        if model.where:
            where.append(model.where)
        if where:
            sql += u'where ' + u' and '.join(where) + '\n\n'
        return sql

    def _create_sql(self, cr, uid, model, context=None):
        context = context or {}
        if fields and context.get('reconvertion_type', '') == 'test':
            return self._create_sql_test(
                cr, uid, model, model.fields_ids, context)
        if fields and context.get('reconvertion_type', '') == 'really do it':
            return self._create_sql_reconvert(
                cr, uid, model, model.fields_ids, context)
        else:
            return ''

    def _process_model_reconvertion(self, cr, uid, ids, context=None):
        sql = ''
        for item in self.browse(cr, uid, ids, context={}):
            for model in item.models_ids:
                if model.status == 'toreconvert':
                    sql += self._create_sql(cr, uid, model, context)
        if sql:
            self.write(
                cr, uid, ids, {'sql_script': sql}, context=context)
        return True

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
        'sql_command': fields.char(
            'Sql reconvertion command', size=128,
            required=False, readonly=False,
            help="Set the SQL reconvertion command.\n"
                 "Sample: '\%s/1000' -> where '\%s' will be replaced by field "
                 "name (actually alias.field_name)"),
        'sql_reverse': fields.char(
            'Sql reverse reconvertion', size=128,
            required=False, readonly=False,
            help="Set the SQL reverse reconvertion command.\n"
                 "Sample: '\%s*1000' -> where '\%s' will be replaced by field "
                 "name (actually alias.field_name)"),
        'precision_ids': fields.one2many(
            'tcv.reconvertion.precision', 'line_id', 'Precision'),
        'sql_script': fields.text('Sql script', readonly=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'sql_command': lambda *a: '\%s/1000',
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
                        tfn = type(field).__name__
                        store = tfn in ('property', 'float') or (
                            tfn in ('function', 'related') and field.store)
                        fields_data.update({
                            field_name: {'fld_type': tfn, 'store': store}})
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

    def button_test_reconvertion(self, cr, uid, ids, context=None):
        context = context or {}
        context.update({'reconvertion_type': 'test'})
        self._process_model_reconvertion(cr, uid, ids, context)
        return True

    def button_do_reconvertion(self, cr, uid, ids, context=None):
        context = context or {}
        context.update({'reconvertion_type': 'really do it'})
        self._process_model_reconvertion(cr, uid, ids, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_reconvertion()


##----------------------------------------------------- tcv_reconvertion_models


class tcv_reconvertion_models(osv.osv):

    _name = 'tcv.reconvertion.models'

    _description = ''

    _rec_name = 'model_id'

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
            'Company rule'),
        'check_currecy': fields.boolean(
            'Check currecy', readonly=False),
        'where': fields.char(
            'Where', size=128, required=False, readonly=False,
            help="Set special where clause for this model"),
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

    _rec_name = 'field_id'

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
             ('reverse', 'Reverse'),
             ('noreconvert', 'No reconvert')],
            string='Method', required=True, readonly=False),
        'rounding': fields.selection(
            [('0.01', '0.01'),
             ('0.5', '0.5'),
             ('0.00001', '0.00001'),
             ('none', 'None')],
            string='Rounding', required=True, readonly=False),
        'store': fields.boolean(
            'Stored', readonly=True),
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


##-------------------------------------------------- tcv_reconvertion_precision


class tcv_reconvertion_precision(osv.osv):

    _name = 'tcv.reconvertion.precision'

    _description = ''

    _rec_name = 'field_id'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.reconvertion', 'Reconvertion', required=True,
            ondelete='cascade'),
        'presicion_id': fields.many2one(
            'decimal.precision', 'Decimal', required=True, ondelete='restrict',
            help="Select decimal presicion settings afected by reconvertion"
            ),
        'original_value': fields.integer(
            'Original', help="Original presicion before reconvertion"),
        'reconvertion_value': fields.integer(
            'Reconvertion', help="Presicion for reconvertion process"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    def on_change_presicion_id(self, cr, uid, ids, presicion_id):
        res = {}
        if presicion_id:
            obj_dp = self.pool.get('decimal.precision')
            dp_brw = obj_dp.browse(cr, uid, presicion_id, context=None)
            res.update({'original_value': dp_brw and dp_brw.digits or 2})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_reconvertion_precision()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

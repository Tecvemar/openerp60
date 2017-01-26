# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_related_annual_sales
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv


__tcv_related_annual_sales_TYPES__ = [
    (10, _('Related partners - Sales (Amount)')),
    (20, _('Related partners - Sales (Slab quantity)')),
    (30, _('Related partners - Sales (Tile quantity)')),
    (40, _('Related partners - Sales (Global quantity)')),
    ]


##---------------------------------------------------- tcv_related_annual_sales


class tcv_related_annual_sales(osv.osv_memory):

    _inherit = 'tcv.monthly.report'

    _name = 'tcv.related.annual.sales'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_related_annual_sales, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Related partners - Annual summary of sales'),
            })
        return data

    def _get_pct_type(self, type):
        res = super(tcv_related_annual_sales, self)._get_pct_type(type)
        return res

    def _exec_sql(self, cr, uid, profit_id, sql, context):
        obj_cfg = self.pool.get('tcv.profit.import.config')
        try:
            obj_cfg.get_profit_db_cursor(
                cr, uid, [profit_id], context=context)
            obj_cfg.exec_sql(sql)
            return obj_cfg.fetchall()
        except:
            raise osv.except_osv(
                _('Error!'),
                _('Profit: SQL Server communication error'))

    def _get_related_partner_sales(self, cr, uid, ids, params, context):
        lines_ord = [
            u'DISTRIBUIDORA ACROPOLIS, C.A',
            u'DISTRIBUIDORA ACROPOLIS GUAYANA, C.A',
            u'DISTRIBUIDORA ACROPOLIS MONAGAS, C.A.',
            u'REVESTIMIENTO DACROPOLIS C.A.',
            u'DISTRIBUIDORA ACROPOLIS MARACAY, C.A',
            u'DISTRIBUIDORA ACROPOLIS BARQUISIMETO, C.A.',
            u'DISTRIBUIDORA ACROPOLIS FALCÓN,C.A.',
            u'GRANITOS DEL ORINOCO, S.A.',
            ]
        sql = """
        select year,
               month,
               partner_id as code, partner_id as name,
               %(amount_field)s as quantity
        from tcv_related_annual_sales
        where year = 2016
        order by 1,2,3
        """ % params
        data = self._exec_sql(
            cr, uid, params.get('profit_id'), sql, context=context)
        return lines_ord, data

    def _get_related_partner_list(self, cr, uid, context):
        partner_list = {}
        obj_partner = self.pool.get('res.partner')
        partner_ids = obj_partner.search(
            cr, uid, [('category_id', '=', 14)])  # Related partners
        for p in obj_partner.browse(cr, uid, partner_ids, context=context):
            partner_list.update({p.id: p.name})
        return partner_list

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __tcv_related_annual_sales_TYPES__, string='Type', required=True,
            readonly=False),
        #~ Must be added to corret % calculation
        'line_ids': fields.one2many(
            'tcv.related.annual.sales.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.related.annual.sales.lines', 'line_id', 'Lines',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.related.annual.sales.lines', 'line_id', 'Lines',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.related.annual.sales.lines', 'line_id', 'Lines',
            readonly=True),
        'profit_id': fields.many2one(
            'tcv.profit.import.config', 'Database name', required=True,
            readonly=False),
        }

    _defaults = {
        'type': lambda *a: 10,
        'remove_zero': lambda *a: True,
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_monthly_lines(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        params = self.get_report_default_params(cr, uid, ids, brw)
        params.update({'profit_id': brw.profit_id.id})
        partner_list = self._get_related_partner_list(cr, uid, context)
        amt_fields = {
            10: 'amount_sales',
            20: 'slab_m2',
            30: 'tile_m2',
            40: 'slab_m2 + tile_m2 - return_m2',
            }
        data = []
        if params['type'] in (10, 20, 30, 40):
            params.update({
                'amount_field': amt_fields.get(params['type'], 'amount_sales'),
                })
            if params['type'] == 10:
                params.update({'digits': 0})
            lines_ord, data_tmp = self._get_related_partner_sales(
                cr, uid, ids, params, context)
            for item in data_tmp:
                data.append([
                    item['year'],
                    item['month'],
                    item['code'],
                    partner_list[item['name']],
                    item['quantity'],
                    ])
        else:
            lines_ord = []
            data = []
        self.load_report_data(cr, uid, ids, lines_ord, data, params, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_related_annual_sales()


##---------------------------------------------- tcv_related_annual_sales_lines


#~ Must be added to corret % calculation
class tcv_related_annual_sales_lines(osv.osv_memory):

    _inherit = 'tcv.monthly.report.lines'

    _name = 'tcv.related.annual.sales.lines'

    _columns = {
        'line_id': fields.many2one(
            'tcv.related.annual.sales', 'Line', required=True,
            ondelete='cascade'),
        }

tcv_related_annual_sales_lines()


##---------------------------------------------------------------------- Parser


class parser_tcv_related_annual_sales(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_related_annual_sales, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        types = {}
        for item in __tcv_related_annual_sales_TYPES__:
            types.update({item[0]: _(item[1])})
        values = {'type': types,
                  }
        return values[type].get(val, '')

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1,fld_2,...')), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

report_sxw.report_sxw(
    'report.tcv.related.annual.sales.report',
    'tcv.related.annual.sales',
    'addons/tcv_monthly_report/report/tcv_monthly_report.rml',
    parser=parser_tcv_related_annual_sales,
    header=False
    )

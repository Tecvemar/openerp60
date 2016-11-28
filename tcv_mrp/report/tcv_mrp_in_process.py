# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_in_process
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_mrp_in_process(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_in_process, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_templates_list': self._get_templates_list,
            'get_subprocess_by_template': self._get_subprocess_by_template,
            'get_summary_by_product': self._get_summary_by_product,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_templates_list(self, obj):
        sql = '''
            select sequence, id, name from tcv_mrp_template
            where output_model is not null
            order by sequence
            '''
        self.cr.execute(sql)
        res = []

        for item in self.cr.fetchall():
            data = {'id': item[1],
                    'name': item[2],
                    'count': 0,
                    'total_pieces': 0,
                    'total_area': 0,
                    'total_cost': 0,
                    }
            for line in obj.line_ids:
                if line.template_id.id == data.get('id'):
                    data['count'] += 1
                    data['total_pieces'] += line.pieces
                    data['total_area'] += line.area
                    data['total_cost'] += line.total_cost
            if data['count']:
                res.append(data)
        data = {'id': 0,
                'name': _('General'),
                'count': 0,
                'total_pieces': 0,
                'total_area': 0,
                'total_cost': 0,
                }
        for item in res:
            data['count'] += item['count']
            data['total_pieces'] += item['total_pieces']
            data['total_area'] += item['total_area']
            data['total_cost'] += item['total_cost']
        res.append(data)
        return res

    def _get_subprocess_by_template(self, obj, template_id):
        res = []
        for line in obj.line_ids:
            if line.template_id.id == template_id:
                res.append(line)
        return res

    def _get_summary_by_product(self, obj):
        data = {}
        for line in obj.line_ids:
            group = line.template_id.name.split()[0]
            product = line.product_id.name
            if not data.get(group):
                data.update({group: {}})
            if not data[group].get(product):
                data[group].update({product: {'total_pieces': 0,
                                              'total_area': 0}})
            data[group][product]['total_pieces'] += line.pieces
            data[group][product]['total_area'] += line.area
        res = []
        for tgroup in data.keys():
            for tproduct in data[tgroup].keys():
                values = {'group': tgroup, 'product': tproduct}
                values.update(data[tgroup][tproduct])
                res.append(values)

        return sorted(
            res, key=lambda elem: "%s %s" % (elem['group'], elem['product']))

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

report_sxw.report_sxw('report.tcv.mrp.in.process.report',
                      'tcv.mrp.in.process',
                      'addons/tcv_mrp/report/tcv_mrp_in_process.rml',
                      parser=parser_tcv_mrp_in_process,
                      header=False
                      )

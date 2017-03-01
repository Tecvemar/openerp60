# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
import cStringIO
import base64


##----------------------------------------- tcv_mrp_finished_product_txt_export

class tcv_label_request_print_prn_export(osv.osv_memory):

    _name = 'tcv.label.request.print.prn.export'

    _description = ''

    _sections = ('<header>', '<body>', '<nextlabel>', '<footer>')

    ##-------------------------------------------------------------------------

    def load_label_template(self, label_template):
        actual_key = ''
        res = {}
        for line in label_template.splitlines(True):
            line_tmp = line[:-2]
            if line_tmp in self._sections:
                actual_key = line_tmp
                res.update({actual_key: ''})
            elif actual_key:
                res[actual_key] = line if res[actual_key] == '' else '%s%s' % (
                    res[actual_key], line)
        return res

    def create_labels(self, label_list, label_template, params=None):
        params = params or {}
        res = label_template['<header>']
        for label in label_list:
            body = ''
            for l in label_template['<body>'].splitlines(True):
                label_number = '%s>6%s' % (
                    label[:-1], label[-1]) if len(label) > 6 else label

                params.update({
                    'label_number': label_number,
                    'label_number2': label,
                    })
                t = l % params
                body += t
            res = ''.join([res, body])
            if label != label_list[-1]:
                res = ''.join((res, label_template['<nextlabel>']))
        res = ''.join((res, label_template['<footer>']))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Filename', 64, readonly=True),
        'prn_file': fields.binary(
            'PRN file', readonly=True, filters='*.prn', help="PRN file name"),
        'label_start': fields.char(
            'Label start', size=16, required=False, readonly=True),
        'label_end': fields.char(
            'Label end', size=16, required=False, readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'block_ref': fields.char(
            'block_ref', size=128, required=False, readonly=False),
        'price_1': fields.float(
            'price_1', digits_compute=dp.get_precision('Account')),
        'tax_1': fields.float(
            'tax_1', digits_compute=dp.get_precision('Account')),
        'price_2': fields.float(
            'price_2', digits_compute=dp.get_precision('Account')),
        'label_date': fields.char(
            'label_date', size=128, required=False, readonly=False),
        'label_template_id': fields.many2one(
            'tcv.label.template', 'Gangsaw label template', required=True,
            readonly=False, ondelete='restrict',
            help="Default label template for gangsaw's labels"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'loaded': fields.boolean(
            'loaded'),
        }

    _defaults = {
        'label_start': lambda *a: 0,
        'label_end': lambda *a: 0,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def button_generate_labels(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        buf = cStringIO.StringIO()
        for item in self.browse(cr, uid, ids, context={}):
            output_prd = item.product_id
            obj_lbl = self.pool.get('tcv.label.request.print.prn.export')
            template = item.label_template_id
            p_name = output_prd.name.split('/')[0].upper()
            for x in ('BLOQUES', '1RA', '2DA', '(POCO MOVIMIENTO)',
                      'LAMINAS', 'RESINADAS', 'PULIDAS', '20MM', '.'):
                p_name = p_name.replace(x, '')
                p_name = p_name.replace('  ', ' ')
            product_name = p_name.strip() if p_name != 'ROSA CARIBE ' \
                else 'CARIBE'
            if not item.label_start.isdigit() or \
                    not item.label_end.isdigit() or \
                    len(item.label_start) != 11 or \
                    len(item.label_end) != 11 or \
                    item.label_start[:-2] != item.label_end[:-2] or \
                    int(item.label_start) > int(item.label_end):
                raise osv.except_osv(
                    _('Error!'),
                    _('Invalid labels sequence'))
            label_list = range(int(item.label_start), int(item.label_end) + 1)
            label_list = map(lambda x: '%011d' % x, label_list)
            label_template = obj_lbl.load_label_template(template.template)
            block_ref = item.block_ref
            price_1 = item.price_1
            tax_1 = item.tax_1
            price_2 = item.price_2
            label_date = item.label_date
            labels = obj_lbl.create_labels(
                label_list, label_template,
                {'product_name': product_name,
                 'block_ref': 'Ref: %s' % block_ref,
                 'price_1': ('PMVP: %.2f | IVA: %.2f' %
                             (price_1, tax_1)).replace('.', ','),
                 'price_2': ('A pagar Bs x m2:%.2f' %
                             (price_2)).replace('.', ','),
                 'label_date': label_date,
                 })
            buf.write(labels)
            out = base64.encodestring(buf. getvalue())
            buf.close()
            file_name = '%s-%s.prn' % (label_list[0], label_list[-1][-2:])
            self.write(
                cr, uid, [item.id], {
                    'prn_file': out, 'name': file_name, 'loaded': True},
                context=context)
            return True

    ##------------------------------------------------------------ on_change...

    def on_change_label(self, cr, uid, ids, label_start, label_end):
        res = {}
        res.update({'Name': None, 'prn_file': None, 'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_label_request_print_prn_export()

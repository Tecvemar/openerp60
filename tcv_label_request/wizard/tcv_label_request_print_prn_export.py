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
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import cStringIO
#~ import base64


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
                #~ if l.find('[[label_number]]') > 0:
                    #~ label_number = '%s>6%s' % (
                        #~ label[:-1], label[-1]) if len(label) > 6 else label
                    #~ t = l.replace('[[label_number]]', label_number)
                #~ elif l.find('[[product_name]]') > 0:
                    #~ t = l.replace('[[product_name]]',
                                  #~ params.get('product_name', ''))
                #~ elif l.find('[[block_ref]]') > 0:
                    #~ t = l.replace('[[block_ref]]',
                                  #~ params.get('block_ref', ''))
                #~ else:
                    #~ t = l
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
        }

    _defaults = {
        'label_start': lambda *a: 0,
        'label_end': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_label_request_print_prn_export()

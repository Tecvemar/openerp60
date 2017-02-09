# -*- encoding: utf-8 -*-
########################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
########################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
import cStringIO
import base64
import unicodedata


##---------------------------------------------tcv_txt_check_export_vzla


class tcv_txt_check_export_vzla(osv.osv_memory):

    _name = 'tcv.txt.check.export.vzla'

    _description = ''

    ##------------------------------------------------------------------

    ##------------------------------------------------ _internal methods

    ##-------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Filename', 64, readonly=True),
        'csv_file': fields.binary('TXT file', readonly=True,
                                  filters='*.txt', help="TXT file name"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------

    ##--------------------------------------------------- public methods

    ##------------------------------------------------- buttons (object)

    def button_create_csv(self, cr, uid, ids, context=None):

        def normalize(s):
            return ''.join((
                c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn'))

        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if not context.get('crw_data'):
            return {}
        else:
            crw_data = context.get('crw_data')
        res = []
        header = '0%10s%05d%20s%017d' % (
            crw_data['company_vat'],
            len(crw_data['check_ids']),
            crw_data['bank_acc_number'],
            int(crw_data['total_amount'] * 100),
            )
        res.append(header)
        for check in crw_data['check_ids']:
            date = time.strftime(
                '%d/%m/%Y', time.strptime(check['date'], '%Y-%m-%d'))
            line = '1%20s%-60s%8s%017d%10sS%-80s' % (
                crw_data['bank_acc_number'],
                normalize(check['beneficiary'][:60]),
                check['number'],
                int(check['amount'] * 100),
                date,
                normalize(check['concept'][:80]),
                )
            res.append(line)
        data = '\r\n'.join(res)
        buf = cStringIO.StringIO()
        buf.write(data.encode('utf-8'))
        output_file = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(
            cr, uid, ids, {
                'csv_file': output_file,
                'name': 'check_list.txt'},
            context=context)

    ##----------------------------------------------------- on_change...

    ##---------------------------------------------- create write unlink

    ##--------------------------------------------------------- Workflow

tcv_txt_check_export_vzla()

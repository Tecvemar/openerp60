# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class tcv_bank_list(osv.osv):

    _name = 'tcv.bank.list'

    _description = ''

    _columns = {
        'code': fields.char('Code', size=4, required=True),
        'name': fields.char('Name', size=32, required=True),
        'active': fields.boolean('Active', required=True),

        }

    _defaults = {
        'code': lambda *a: '',
        'name': lambda *a: '',
        'active': lambda *a: True,
        }

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'The code must be unique!'),
        ]

tcv_bank_list()


class tcv_bounced_cheq_motive(osv.osv):

    _name = 'tcv.bounced.cheq.motive'

    _description = 'Motivos de devolucion de cheques del modulo tcv_bounced_cheq'

    _columns = {
        'name': fields.char('Motive', size=64, required=True, readonly=False),
       }

    _defaults = {
        'name': lambda *a: '',
        }

    _sql_constraints = [
        ('motive_uniq', 'UNIQUE(name)', 'The motive must be unique!'),
        ]

tcv_bounced_cheq_motive()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

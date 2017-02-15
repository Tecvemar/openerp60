# -*- encoding: utf-8 -*-
##############################################################################
#    
#~ 
#~ 
#
##############################################################################
from osv import fields,osv

class tcv_bank_config_detail(osv.osv):
    
    _inherit = "tcv.bank.config.detail"
    
    _columns = {
        'use_bounced_cheq':fields.boolean('Use Bounced cheq', help='Moves of this kind can generate a bounced cheq', required=True),
        }

    _defaults = {
        'use_bounced_cheq': lambda *a: False,
        }
        
tcv_bank_config_detail()


class tcv_bounced_cheq_motive(osv.osv):

    _inherit = "tcv.bounced.cheq.motive"

    _columns = {
        'use_fee': fields.boolean('Use fee', required=True, readonly=False, help='Select if you what to use a fee. It requires that you enable the configuration of the company:: Charge fee for bounced check' ),
        'need_note': fields.boolean('Need aditional note', required=True, readonly=False),
       }
        

    _defaults = {
        'use_fee': lambda *a: False,
        'need_note': lambda *a: False,
        }

    _sql_constraints = [
        ]

tcv_bounced_cheq_motive()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

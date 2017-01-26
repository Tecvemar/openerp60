# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##-------------------------------------------------------------- tcv_mrp_config


class tcv_mrp_config(osv.osv):

    _inherit = 'tcv.mrp.config'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'label_template_id': fields.many2one(
            'tcv.label.template', 'Gangsaw label template', required=True,
            readonly=False, ondelete='restrict',
            help="Default label template for gangsaw's labels"),
        }

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_config()

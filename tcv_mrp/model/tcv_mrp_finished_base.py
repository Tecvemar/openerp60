# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 31/10/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------- tcv_mrp_finished_base


class tcv_mrp_finished_base(osv.osv):

    _name = 'tcv.mrp.finished.base'

    _inherit = 'tcv.mrp.basic.task'

    _stock_picking_type = 'in'

    def _template_params(self):
        res = [
        ]
        return res

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def get_task_runtime_sumary(self, cr, uid, ids_str, context=None):
        return {}

    ##------------------------------------------------------------ on_change...

    def on_change_run_time2(self, cr, uid, ids, date_start, date_end):
        if date_end:
            date_end = '%s 00:00:40' % date_end[:10]
            date_start = '%s 00:00:00' % date_end[:10]
            return {'value': {'run_time': self._compute_run_time(
                cr, uid, date_start, date_end),
                'date_start': date_start, 'date_end': date_end}}
        return {}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_finished_base()

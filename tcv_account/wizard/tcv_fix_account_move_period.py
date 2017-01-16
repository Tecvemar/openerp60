# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-26
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc
import logging
logger = logging.getLogger('server')

##------------------------------------------------- tcv_fix_account_move_period


class tcv_fix_account_move_period(osv.osv_memory):

    _name = 'tcv.fix.account.move.period'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        if context is None:
            context = {}
        res = super(tcv_fix_account_move_period, self).default_get(
            cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('account.move')
        move = move_obj.browse(cr, uid, record_id, context=context)
        if move:
            if move.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Only moves in draft must be fixed'))
            res.update({
                'move_id': move.id,
                'period_id': move.period_id.id,
                'date': move.date,
                })
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'period_id': fields.many2one(
            'account.period', 'Period', required=True, ondelete="restrict",
            domain=[('state', '<>', 'done')]),
        'date': fields.date(
            'Date', required=True, readonly=False, select=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        obj_per = self.pool.get('account.period')
        for item in self.browse(cr, uid, ids, context={}):
            line_ids = []
            period_id = obj_per.find(cr, uid, item.date)[0]
            if period_id != item.period_id.id:
                raise osv.except_osv(
                    _('Error!'),
                    _('New date must be inside new period'))
            for line in item.move_id.line_id:
                line_ids.append(line.id)
            if line_ids:
                data = {
                    'move_id': item.move_id.id,
                    'period_id': item.period_id.id,
                    'date': item.date,
                    'line_ids': (str(line_ids)[1:-1]).replace('L', ''),
                    }
                cr.execute('''
                    UPDATE account_move SET
                    period_id = %(period_id)s,
                    date = '%(date)s'
                    WHERE id = %(move_id)s''' % data)
                cr.execute('''
                    UPDATE account_move_line SET
                    period_id = %(period_id)s,
                    date = '%(date)s'
                    WHERE id in (%(line_ids)s)''' % data)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_fix_account_move_period()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

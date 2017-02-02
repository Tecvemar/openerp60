# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-08-05
#    Version: 1.0
#
#    Description:
#
#
##############################################################################

from datetime import datetime
from osv import fields, osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time
import netsvc

##------------------------------------------------------------------ tcv_technical_support_request


class tcv_technical_support_request(osv.osv):

    _name = 'tcv.technical.support.request'

    _description = ''

    ##-------------------------------------------------------------------------

    IMPORTANCE_SELECTION = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ]

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('inprogress', 'In Progress'),
        ('done','Done'),
        ]

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', required=True,
            states={'draft': [('readonly', False)]}, readonly=True,
            select=True, ondelete='restrict'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'department_id': fields.many2one(
            'hr.department', 'User department',
            states={'draft': [('readonly', False)]}, readonly=True,
            required=True, select=True, ondelete='restrict'),
        'date_request': fields.date(
            'Date request', required=True,
            states={'draft': [('readonly', False)]}, readonly=True,
            select=True),
        'type_id': fields.many2one(
            'tcv.technical.support.request.type', 'Type', required=True,
            states={'draft': [('readonly', False)]},
            readonly=True, ondelete='restrict'),
        'importance':fields.selection(
            IMPORTANCE_SELECTION, string='Importance', required=True,
            states={'draft': [('readonly', False)]}, readonly=True),
        'date_start_request': fields.datetime(
            'Date start request', states={
                'confirmed': [('readonly', False),('required', True)]},
            required=False, readonly=True,  select=True),
        'date_end_request': fields.datetime(
            'Date end request', states={
                'inprogress': [('readonly', False),('required', True)]},
            readonly=True, required=False, select=True),
        'request': fields.text(
            'Request', states={'draft': [('readonly', False)]}, readonly=True,
            required=True),
        'narration': fields.text(
            'Notes', states={'inprogress': [(
                'readonly', False),('required', True)]},
            readonly=True, required=False),
        'user_developer': fields.many2one(
            'res.users', 'Developer', readonly=True, ondelete='restrict'),
        'user_processor': fields.many2one(
            'res.users', 'Processor', states={
                'confirmed': [('readonly', False),('required', True)]},
            readonly=True, required=False, select=True, ondelete='restrict'),
        'user_validator': fields.many2one(
            'res.users', 'Validator', states={
                'inprogress': [('readonly', False),('required', True)]},
            readonly=True, required=False, select=True, ondelete='restrict'),
        'user_receiver': fields.many2one(
            'res.users', 'Receiver',
            states={'inprogress': [('readonly', False)]}, readonly=True,
            select=True, ondelete='restrict'),
        'state':fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        }

    _defaults = {
        'name': lambda *a: '/',
        'user_developer': lambda s, c, u, ctx: u,
        'date_request': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state':'draft'}
        res = self.write(cr,uid,ids,vals,context)
        return res

    def button_cancelled(self, cr, uid, ids, context=None):
        vals = {'state':'cancelled'}
        res = self.write(cr,uid,ids,vals,context)
        return res

    def button_confirmed(self, cr, uid, ids, context=None):
        vals = {'state':'confirmed'}
        res = self.write(cr,uid,ids,vals,context)
        return res

    def button_inprogress(self, cr, uid, ids, context=None):
        vals = {'state':'inprogress'}
        res = self.write(cr,uid,ids,vals,context)
        return res

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state':'done'}
        res = self.write(cr,uid,ids,vals,context)
        return res

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
            get(cr, uid, 'tcv.technical.support.request')})
        res = super(tcv_technical_support_request, self).create(cr, uid, vals, context)
        return res



    ##---------------------------------------------------------------- Workflow

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_cancelled(self, cr, uid, ids, *args):
        return True

    def test_confirmed(self, cr, uid, ids, *args):
        return True

    def test_inprogress(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        return True

tcv_technical_support_request()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

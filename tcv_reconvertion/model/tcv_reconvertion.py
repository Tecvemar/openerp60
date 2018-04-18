# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-04-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# ~ from datetime import datetime
from osv import fields, osv
# ~ from tools.translate import _
# ~ import pooler
# ~ import decimal_precision as dp
# ~ import time
# ~ import netsvc

##------------------------------------------------------------ tcv_reconvertion


class tcv_reconvertion(osv.osv):

    _name = 'tcv.reconvertion'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'date': fields.date(
            'Date', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'models_ids': fields.one2many(
            'reconverton.models', 'line_id', 'Models'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_reconvertion()


##--------------------------------------------------------- class_name


class tcv_reconverton_models(osv.osv):

    _name = 'tcv_reconverton.models'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.reconvertion', 'Reconvertion', required=True,
            ondelete='cascade'),
        'ir_model': fields.many2one(
            'ir.model', 'Model', required=True, ondelete='restrict',
            help="Model with data to be reconvertereds"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_reconverton_models()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

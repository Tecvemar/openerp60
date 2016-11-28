# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-30
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

##---------------------------------------------------------- tcv_driver_vehicle


class tcv_driver_vehicle(osv.osv):

    _name = 'tcv.driver.vehicle'

    _description = ''

    _order = 'code'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            if item.type == 'vehicle':
                name = '[%s] %s (%s)' % (item.code, item.name, item.ident)
            else:
                name = '[%s] %s' % (item.code, item.name)
            res.append((item.id, name))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search(
                cr, user, [('code', '=like', name + "%")] + args,
                limit=limit)
            if not ids:
                ids = self.search(
                    cr, user, [('ident', '=like', '%' + name + '%')] + args,
                    limit=limit)
            if not ids:
                ids = self.search(
                    cr, user, [('name', operator, name)] + args,
                    limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    ##--------------------------------------------------------- function fields

    _columns = {
        'code': fields.char(
            'Code', size=16, required=True, readonly=True, select=1),
        'name': fields.char(
            'Name/Brand', size=64, required=True, readonly=False,
            help="The name of driver or Brand of vehicle"),
        'name2': fields.char(
            'Phone/Model', size=64, required=False, readonly=False,
            help="The phone number of driver or model of vehicle"),
        'ident': fields.char(
            'Identification', size=16, required=True, readonly=False, select=1,
            help="Driver's ID or Vehicles's plate"),
        'type': fields.selection(
            [('driver', 'Driver'), ('vehicle', 'Vehicle')],
            string='Type', required=True, readonly=False),
        'active': fields.boolean(
            'Active', required=True),
        }

    _defaults = {
        'code': lambda *a: '/',
        'active': True,
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, type)', 'The code must be unique!'),
        ('ident_uniq', 'UNIQUE(ident, type)',
         'The Identification must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def fields_get(self, cr, uid, fields=None, context=None):
        result = super(tcv_driver_vehicle, self).fields_get(cr, uid, fields,
                                                            context)
        if context.get('driver_vehicle_type'):
            labels = {'driver': {'ident': _('ID'),
                                 'name': _('Name'),
                                 'name2': _('Phone'),
                                 },
                      'vehicle': {'ident': _('Plate'),
                                  'name': _('Brand'),
                                  'name2': _('Model'),
                                  },
                      }
            for item in labels[context['driver_vehicle_type']].items():
                if result.get(item[0]):
                    result[item[0]].update({'string': item[1]})
        return result

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if vals.get('code', '/') == '/':
            secuence = 'tcv.%s' % vals['type']
            vals.update({'code': self.pool.get('ir.sequence').
                        get(cr, uid, secuence)})
        res = super(tcv_driver_vehicle, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_driver_vehicle()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

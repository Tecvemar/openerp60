# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2016-03-31
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------ tcv_mrp_gangsaw_params


class tcv_mrp_gangsaw_params(osv.osv):

    _name = 'tcv.mrp.gangsaw.params'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'template_id': fields.many2one(
            'tcv.mrp.template', 'Task template', required=True,
            readonly=False, ondelete='restrict',
            domain=[('res_model', '=', 'tcv.mrp.gangsaw')]),
        'whell_amp': fields.integer(
            'Whell amp', help="Max. whell amp"),
        'pump_amp': fields.integer(
            'Pump amp', help="Max. pump amp"),
        'tens_preasure': fields.float(
            'Tensors preasure', digits_compute=dp.get_precision('Account'),
            help="Tensors preasure in tons"),
        'viscosity': fields.float(
            'Viscosity', digits_compute=dp.get_precision('Account'),
            help="Fluid viscosity"),
        'max_length': fields.float(
            'Max length (m)', digits_compute=dp.get_precision('Product UoM'),
            help="Max block length"),
        'max_heigth': fields.float(
            'Max heigth (m)', digits_compute=dp.get_precision('Product UoM'),
            help="Max block heigth"),
        'max_width': fields.float(
            'Max width (m)', digits_compute=dp.get_precision('Product UoM'),
            help="Max block width"),
        'min_steel_grit': fields.float(
            'Min steel grit', digits_compute=dp.get_precision('Product UoM'),
            help="Min dry steel grit"),
        'max_steel_grit': fields.float(
            'Max steel grit', digits_compute=dp.get_precision('Product UoM'),
            help="Max dry steel grit"),
        'params_ids': fields.one2many(
            'tcv.mrp.gangsaw.params.extra', 'gangsaw_params_id',
            'Extra params'),
        'narration': fields.text(
            'Notes', readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('template_uniq', 'UNIQUE(template_id)',
         'The template must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_size(self, cr, uid, ids, length, heigth, width):
        obj_uom = self.pool.get('product.uom')
        length, heigth, width = obj_uom.adjust_sizes(length, heigth, width)
        res = {'value': {'max_length': length,
                         'max_heigth': heigth,
                         'max_width': width,
                         }}
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_params()


##------------------------------------------------ tcv_mrp_gangsaw_params_extra


class tcv_mrp_gangsaw_params_extra(osv.osv):

    _name = 'tcv.mrp.gangsaw.params.extra'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'gangsaw_params_id': fields.many2one(
            'tcv.mrp.gangsaw.params', 'Order', required=True,
            ondelete='cascade'),
        'hardness': fields.integer(
            'Hardness (1-5)', help="1=Soft, 3=Medium, 5=Hard"),
        'cut_down_feed': fields.integer(
            'Cut down feed (mm/h)',
            help="Recomended cut down feed (mm/h)"),
        'interval': fields.integer(
            'Interval (min)', help="Time between steel grit feed (min)"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('hardness_range', 'CHECK(hardness between 1 and 5)',
         'The hardness must be in 1-5 range!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_params_extra()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

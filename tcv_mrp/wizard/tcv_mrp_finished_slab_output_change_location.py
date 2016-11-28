# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
##############################################################################


from osv import fields, osv

##-------------------------------- tcv_mrp_finished_slab_output_change_location


class tcv_mrp_finished_slab_output_change_location(osv.osv_memory):

    _name = 'tcv.mrp.finished.slab.output.change.location'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'from_slab': fields.many2one(
            'tcv.mrp.finished.slab.output', 'From slab', required=True),
        'to_slab': fields.many2one(
            'tcv.mrp.finished.slab.output', 'To slab', required=True),
        'location_id': fields.many2one(
            'stock.location', 'New location', required=True, select=True),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def relocate_slabs(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_slb = self.pool.get('tcv.mrp.finished.slab')
        obj_out = self.pool.get('tcv.mrp.finished.slab.output')
        wz = self.browse(cr, uid, ids[0], context=context)
        task = obj_slb.browse(
            cr, uid, context. get('task_ids', [0])[0], context=context)
        update_ids = []
        for output in task.output_ids:
            if output.id >= wz.from_slab.id and output.id <= wz.to_slab.id:
                update_ids.append(output.id)
        if update_ids:
            obj_out.write(
                cr, uid, update_ids, {'location_id': wz.location_id.id},
                context=context)

    def button_done(self, cr, uid, ids, context):
        if context is None:
            context = {}
        self.relocate_slabs(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_finished_slab_output_change_location()

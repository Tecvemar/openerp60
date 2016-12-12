# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 03/10/2012
#    Version: 0.0.0.0
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

##---------------------------------------------------------- tcv_mrp_subprocess


class tcv_mrp_subprocess(osv.osv):

    _name = 'tcv.mrp.subprocess'

    _description = ''

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        for i in self.browse(cr, uid, ids, context):
            res.append((i.id, '%s (%s) ' % (i.name or '', i.ref)))
        return res

    ##-------------------------------------------------------------------------

    def _compute_all(self, cr, uid, ids, name, arg, context=None):
        context = context or {}
        if not len(ids):
            return []
        res = {}
        for item in self.browse(cr, uid, ids, context={}):

            obj_task = self.pool.get(item.template_id.res_model.model)
            task_name = ''
            task_state = 'new'
            if obj_task:
                task_ids = obj_task.search(
                    cr, uid, [('parent_id', '=', item.id)])
                if task_ids:
                    task = obj_task.browse(cr, uid, task_ids[0],
                                           context=context)
                    task_name = '%s / %s' % (task.name, task.task_info) \
                                if task_name else '%s' % task.task_info
                    task_state = task.state

            if item.template_id.output_model.model:
                obj_out = self.pool.get(item.template_id.output_model.model)
                progress = obj_out._calc_output_progress(
                    cr, uid, item.id, context) if obj_out else 0
            else:  # if no output_model then end of process
                if obj_task and task_ids:
                    if task.state == 'draft':
                        progress = 50
                    else:
                        if item.template_id.res_model.name == \
                                'tcv.mrp.finished.slab' and \
                                task and task.picking_id:
                            if task.picking_id.state == 'draft':
                                progress = 70
                            elif task.picking_id.state == 'confirmed':
                                progress = 80
                            elif task.picking_id.state == 'assigned':
                                progress = 90
                            elif task.picking_id.state == 'done':
                                progress = 100
                            else:
                                progress = 75
                        else:
                            progress = 100
                else:
                    progress = 0

            res[item.id] = {'progress': progress,
                            'task_name': task_name,
                            'state': task_state}
        return res

    def _state_search(self, cursor, user, obj, name, args, context=None):
        if not len(args):
            return []
        param = "%s %s '%s'" % args[0]
        cursor.execute('''
        select id from (
            select sp.id, COALESCE(g.state, '') ||
                      COALESCE(p.state, '') ||
                      COALESCE(r.state, '') ||
                      COALESCE(w.state, '') ||
                      COALESCE(f.state, '') as state
            from tcv_mrp_subprocess sp
            left join tcv_mrp_gangsaw g on sp.id = g.parent_id and
                sp.template_id in (
                select t1.id from tcv_mrp_template t1
                left join ir_model m1 on t1.res_model = m1.id
                where m1.model = 'tcv.mrp.gangsaw')
            left join tcv_mrp_polish p on sp.id = p.parent_id and
                sp.template_id in (
                select t1.id from tcv_mrp_template t1
                left join ir_model m1 on t1.res_model = m1.id
                where m1.model = 'tcv.mrp.polish')
            left join tcv_mrp_resin r on sp.id = r.parent_id and
                sp.template_id in (
                select t1.id from tcv_mrp_template t1
                left join ir_model m1 on t1.res_model = m1.id
                where m1.model = 'tcv.mrp.resin')
            left join tcv_mrp_finished_slab f on sp.id = f.parent_id and
                sp.template_id in (
                select t1.id from tcv_mrp_template t1
                left join ir_model m1 on t1.res_model = m1.id
                where m1.model = 'tcv.mrp.finished.slab')
            left join tcv_mrp_waste_slab w on sp.id = w.parent_id and
                sp.template_id in (
                select t1.id from tcv_mrp_template t1
                left join ir_model m1 on t1.res_model = m1.id
                where m1.model = 'tcv.mrp.waste.slab')
            ) as q
        where %s
        ''' % param)
        res = cursor.fetchall()
        return [('id', 'in', [x[0] for x in res])]

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Reference', size=16, required=True, readonly=True),
        'name': fields.char(
            'Name', size=32, required=False, readonly=False),
        'template_id': fields.many2one(
            'tcv.mrp.template', 'Task template', required=True,
            readonly=False, ondelete='restrict'),
        'process_id': fields.many2one(
            'tcv.mrp.process', 'Process', required=True, ondelete='cascade'),
        'prior_id': fields.many2one(
            'tcv.mrp.subprocess', 'Prior task', readonly=False,
            domain="[('process_id','=',process_id)]", ondelete='restrict'),
        'state': fields.function(
            _compute_all, method=True, type='char', size=16, string='State',
            multi='all', fnct_search=_state_search),
        'progress': fields.function(
            _compute_all, method=True, type='float', string='Progress',
            digits=(8, 2), multi='all'),
        'task_name': fields.function(
            _compute_all, method=True, type='char', size=96,
            string='Task name / Info', multi='all'),
        }

    _defaults = {
        'ref': lambda *a: '/',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def button_detail(self, cr, uid, ids, context=None):
        if not ids:
            return []
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        so_brw = self.browse(cr, uid, ids[0], context={})
        model = so_brw.template_id.res_model.model
        def_context = {'default_parent_id': so_brw.id,
                       'template_id': so_brw.template_id.id}
        obj_task = self.pool.get(model)
        task_ids = obj_task.search(cr, uid, [('parent_id', '=', so_brw.id)])
        if task_ids:
            res.update({'res_id': task_ids[0]})
        else:
            def_context.update(
                obj_task.load_default_values(cr, uid, so_brw.id, context))
        res.update({
            'name': so_brw.template_id.name,
            'view_mode': 'form',
            'view_id': self.pool.get('ir.ui.view').
            search(cr, uid, [('model', '=', model)]),
            'view_type': 'form',
            'res_model': model,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': def_context
            })
        return res

    ##------------------------------------------------------------ on_change...

    def on_change_template(self, cr, uid, ids, name, template):
        res = {}
        if template:
            res = {'value': {'name': self.pool.get('tcv.mrp.template').
                             browse(cr, uid, template, context=None).name}}
        return res

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.mrp.subprocess')})
        res = super(tcv_mrp_subprocess, self).create(cr, uid, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context=context):
            if item.state in ('draft', 'new'):
                used_ids = self.search(cr, uid, [('prior_id', '=', item.id)])
                if used_ids:
                    used_brw = self.browse(cr, uid, used_ids, context={})[0]
                    raise osv.except_osv(
                        _('Invalid action !'),
                        _('Cannot delete subprocess referenced by other (%s)!')
                        % used_brw.ref)
                unlink_ids.append(item.id)
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete subprocess that are already Done!'))
        res = super(tcv_mrp_subprocess, self). \
            unlink(cr, uid, unlink_ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_mrp_subprocess()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

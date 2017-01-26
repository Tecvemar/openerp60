# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez.
#    Creation Date: 27/09/2012
#    Version: 0.0.0.1
#
#    Description: Crear solicitudes para hacer etiquetas.
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc
import cStringIO
import base64


##----------------------------------------------------------- tcv_label_request

class tcv_label_request(osv.osv):

    _name = 'tcv.label.request'

    _description = ''

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('required', 'Required'),
        ('printed', 'Printed'),
        ('delivered', 'Delivered')
        ]

    TYPE_SELECTION = [
        ('national', 'National'),
        ('import', 'Import'),
        ('block', 'Block')
        ]

    ##-------------------------------------------------------------------------

    def button_calculate_click(self, cr, uid, ids, context=None):
        return True

    def _get_next_label_number(self, cr, uid, context=None):
        res = {}
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context).company_id.id
        obj_seq = self.pool.get('ir.sequence')
        seq_ids = obj_seq.search(cr, uid, [('name', '=', 'Label sequence'),
                                           ('company_id', '=', company_id)])
        if seq_ids:
            seq = obj_seq.browse(cr, uid, seq_ids[0], context)
            res = {
                'label_start': '%s' % seq.number_next,
                'label_end': '%s' % (
                    seq.number_next + seq.number_increment - 1),
                'quantity': seq.number_increment}
        return res

    ##--------------------------------------------------------- function fields

    def _calc_label(self, cr, uid, type, lot_prefix, prod_lot_id, quantity,
                    label_asigned, context=None):
        if label_asigned:
            return {}
        if type == 'block':
            lot_prefix = lot_prefix or 'XXX'
            prod_lot_id = '%06d' % prod_lot_id
            qty = '%02d' % quantity if quantity < 100 else 'XX'
            res = {
                'label_start': '%s%s01' % (lot_prefix, prod_lot_id),
                'label_end': '%s%s%s' % (lot_prefix, prod_lot_id, qty),
                'quantity': quantity,
                }
        else:
            res = self._get_next_label_number(cr, uid, context)
        return res

    def print_label(self, cr, uid, ids, context=None):
        buf = cStringIO.StringIO()
        if not ids:
            return []
        res = {}
        so_brw = self.browse(cr, uid, ids[0], context={})
        if not so_brw.output_product_id:
            raise osv.except_osv(
                _('Error!'),
                _('Must select an output product'))
        output_prd = so_brw.output_product_id
        obj_lbl = self.pool.get('tcv.label.request.print.prn.export')
        obj_cfg = self.pool.get('tcv.mrp.config')
        obj_tmpl = self.pool.get('tcv.label.template')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        else:
            raise osv.except_osv(_('Error!'),
                                 _('Please set a valid configuration '))
        template = obj_tmpl.browse(
            cr, uid, mrp_cfg.label_template_id.id, context=context)
        p_name = output_prd.name.split('/')[0].upper()
        for x in ('BLOQUES', '1RA', '2DA', '(POCO MOVIMIENTO)',
                  'LAMINAS', 'RESINADAS', 'PULIDAS', '20MM', '.'):
            p_name = p_name.replace(x, '')
            p_name = p_name.replace('  ', ' ')
        product_name = p_name.strip() if p_name != 'ROSA CARIBE ' else 'CARIBE'
        label_list = range(int(so_brw.label_start), int(so_brw.label_end) + 1)
        label_list = map(lambda x: '%011d' % x, label_list)
        label_template = obj_lbl.load_label_template(template.template)
        block_ref = so_brw.gangsaw_ids \
            and so_brw.gangsaw_ids[0].block_ref or ''
        tax = 0.12
        base_price = so_brw.base_price or output_prd.property_list_price
        price_1 = round(base_price * 1.6, 2)
        tax_1 = round(price_1 * tax, 2)
        price_2 = round(price_1 + tax_1, 2)
        date = so_brw.date if so_brw.date >= '2015-11-01' else '2015-11-01'
        fch_date = time.strptime(date, '%Y-%m-%d')
        mm = ('', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
              'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic')
        label_date = '%s/%04d' % (mm[fch_date.tm_mon], fch_date.tm_year)
        labels = obj_lbl.create_labels(
            label_list, label_template,
            {'product_name': product_name,
             'block_ref': 'Ref: %s' % block_ref,
             'price_1': ('PMVP: %.2f | IVA: %.2f' % (price_1,
                                                     tax_1)).replace('.', ','),
             'price_2': ('A pagar Bs x m2: %.2f' % (price_2)).replace('.', ','),
             'label_date': label_date,
             })
        buf.write(labels)
        out = base64.encodestring(buf. getvalue())
        buf.close()
        file_name = '%s-%s.prn' % (label_list[0], label_list[-1][-2:])
        #~ Save base_price
        self.write(
            cr, uid, [so_brw.id], {'base_price': base_price}, context=context)
        res.update({
            'name': _('Create PRN file'),
            'type': 'ir.actions.act_window',
            'res_model': 'tcv.label.request.print.prn.export',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'form',
            'nodestroy': True,
            'target': 'new',
            'domain': "",
            'context': {'default_prn_file': out,
                        'default_name': file_name,
                        'default_label_start': so_brw.label_start,
                        'default_label_end': so_brw.label_end,
                        }
            })
        return res

    _order = 'name desc'

    _columns = {
        'name': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'type': fields.selection(
            TYPE_SELECTION, string='Label type', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            readonly=True, states={'draft': [('readonly', False)]},
            domain="[('stock_driver', '=', 'block')]"),
        'output_product_id': fields.many2one(
            'product.product', 'Output product', ondelete='restrict',
            domain="[('stock_driver', 'in', ('slab', 'tile'))]",
            help="Finished product's name used for print labels"),
        'base_price': fields.float(
            'Base price', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]},
            help="Finished product's price used for print labels"),
        'prod_lot_id': fields.integer(
            'Block/Label #', readonly=True,
            states={'draft': [('readonly', False)]}),
        'quantity': fields.integer(
            'Quantity', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'label_start': fields.char(
            'Label start', size=16, required=False, readonly=True),
        'label_end': fields.char(
            'Label end', size=16, required=False, readonly=True),
        'note': fields.char(
            'Note', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        'user_id': fields.many2one(
            'res.users', 'Required by', readonly=True, select=True,
            ondelete='restrict'),
        'user_id_asigned': fields.many2one(
            'res.users', 'Assigned to', readonly=False, select=True,
            ondelete='restrict'),
        'label_asigned': fields.boolean(
            'Label asigned'),
        'gangsaw_ids': fields.one2many(
            'tcv.mrp.gangsaw.blocks', 'label_id', 'Gangsaw',
            readonly=True, ondelete='set null'),
        }

    _defaults = {
        'name': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'draft',
        'user_id': lambda s, c, u, ctx: u,
        'user_id_asigned': lambda *a: 43,
        'label_asigned': lambda *a: False,
        }

    _sql_constraints = [
        ('prod_lot_id', 'CHECK(prod_lot_id between 0 and 999999)',
         'The block number must be in 1 to 999999 range'),
        ('quantity', 'CHECK(quantity between 1 and 500)',
         'The quantity must be in 1 to 500 range'),
        ('label_start_uniq', 'UNIQUE(label_start)',
         'The label start must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    def _notify_users(self, cr, uid, ids, context=None):
        request = self.pool.get('res.request')
        for label in self.browse(cr, uid, ids, context=context):
            if uid != label.user_id.id:
                rq_id = request.create(
                    cr, uid, {
                        'name': _("Printed labels"),
                        'act_from': uid,
                        'act_to': label.user_id.id,
                        'body': _('The %s label was printed') % label.name,
                        'trigger_date': time.strftime(_('%Y-%m-%d %H:%M:%S'))
                        }, context)
                request.request_send(cr, uid, [rq_id])
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_label_request(
            self, cr, uid, ids, type, product_id, prod_lot_id,
            quantity, label_asigned):
        res = {}
        if type != 'block':
            product_id = 0
            prod_lot_id = 0
            res.update({'product_id': product_id,
                        'prod_lot_id': prod_lot_id})
        lot_prefix = self.pool.get('product.product').browse(
            cr, uid, product_id, context=None).lot_prefix if product_id \
            else False
        if not label_asigned:
            res.update(self._calc_label(
                cr, uid, type, lot_prefix, prod_lot_id,
                quantity, label_asigned, context=None))
        if res:
            return {'value': res}
        else:
            return {}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(
                cr, uid, 'tcv.label.request')})
        lot_prefix = self.pool.get('product.product').browse(
            cr, uid, vals.get('product_id'), context).lot_prefix \
            if vals.get('type') == 'block' else ''
        data = self._calc_label(
            cr, uid, vals.get('type'), lot_prefix, vals.get('prod_lot_id'),
            vals.get('quantity'), vals.get('label_asigned'), context)
        vals.update(data)
        res = super(tcv_label_request, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        obj_prod = self.pool.get('product.product')
        data = {}
        for label in self.browse(cr, uid, ids, context=context):
            type = vals.get('type', label.type)
            if not vals.get('label_start') and not vals.get('label_end'):
                product_id = vals.get('product_id', label.product_id.id)
                lot_prefix = obj_prod.browse(
                    cr, uid, product_id, context).lot_prefix \
                    if type == 'block' else False
                prod_lot_id = vals.get('prod_lot_id', label.prod_lot_id)
                quantity = vals.get('quantity', label.quantity)
                data = self._calc_label(
                    cr, uid, type, lot_prefix, prod_lot_id, quantity,
                    vals.get('label_asigned', label.label_asigned), context)
        if type != 'block':
            data.update({'product_id': None,
                         'prod_lot_id': None})
        vals.update(data)
        res = super(tcv_label_request, self).write(cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for label in self.browse(cr, uid, ids, context={}):
            if label.state in ('draft'):
                unlink_ids.append(label.id)
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete a label when state <> "Draft"!'))
        return super(tcv_label_request, self).unlink(
            cr, uid, unlink_ids, context)

    ##---------------------------------------------------------------- Workflow

    def test_required(self, cr, uid, ids, *args):
        for label in self.browse(cr, uid, ids, context={}):
            if label.type == 'block':
                if label.quantity >= 100:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The quantity must be < 100'))
                if label.prod_lot_id == 0:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must indicate a block number'))
                if not label.product_id.lot_prefix:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must indicate a product\'s lot prefix'))
        return True

    def button_required(self, cr, uid, ids, context=None):
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context).company_id.id
        vals = {'state': 'required'}
        res = self.write(cr, uid, ids, vals, context)
        obj_seq = self.pool.get('ir.sequence')
        obj_lbl = self.pool.get('tcv.label.request')
        seq_ids = obj_seq.search(
            cr, uid, [('code', '=', 'tcv.label.sequence'),
                      ('company_id', '=', company_id)])
        update_labels = False
        for label in self.browse(cr, uid, ids, context={}):
            if label.type in ('national', 'import') and \
                    not label.label_asigned:
                label_start = obj_seq.get(cr, uid, 'tcv.label.sequence')
                seq = obj_seq.browse(cr, uid, seq_ids[0], context)
                label_end = '%s' % (
                    int(label_start) + seq.number_increment - 1)
                obj_lbl.write(
                    cr, uid, [label.id], {'label_start': label_start,
                                          'label_end': label_end,
                                          'quantity': seq.number_increment,
                                          'label_asigned': True}, context)
                update_labels = True
        if update_labels:
            lbl_ids = obj_lbl.search(
                cr, uid, [('type', 'in', ('national', 'import')),
                          ('state', '=', 'draft'),
                          ('label_asigned', '=', False)])
            if lbl_ids:
                label_start = '%s' % (int(label_end) + 1)
                label_end = '%s' % (
                    int(label_start) + seq.number_increment - 1)
                obj_lbl.write(
                    cr, uid, lbl_ids, {'label_start': label_start,
                                       'label_end': label_end,
                                       'quantity': seq.number_increment},
                    context)
        return res

    def button_printed(self, cr, uid, ids, context=None):
        vals = {'state': 'printed'}
        res = self.write(cr, uid, ids, vals, context)
        self._notify_users(cr, uid, ids, context=None)
        return res

tcv_label_request()


##---------------------------------------------------------- tcv_label_template


class tcv_label_template(osv.osv):

    _name = 'tcv.label.template'

    _description = ''

    TYPE_SELECTION = [
        ('national', 'National'),
        ('import', 'Import'),
        ('block', 'Block')
        ]

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _order = 'name desc'

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'type': fields.selection(
            TYPE_SELECTION, string='Label type', required=True,
            readonly=False),
        'template': fields.text(
            'Template', readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_label_template()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

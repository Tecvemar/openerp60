# -*- coding: utf-8 -*-
"""
    Company: Tecvemar, c.a.
    Author: Juan V. Márquez L.
    Creation Date:
    Version: 0.0.0.0

    Description:

"""
##############################################################################
#
#  Add extra data imported from sale.order
#  test_sale_order workflow validations
#
##############################################################################
#~ from osv import fields,osv
#~ import decimal_precision as dp
#~ from tools.translate import _
#~ from datetime import datetime, timedelta
#~ import netsvc
#~ from dateutil.relativedelta import relativedelta
#~ import time


class sale_order_line(osv.osv):


    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Dont confirm a sale order if not have lots"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.purchase_order_line_id.id != False:
               raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sales order line because have a purchase order related!'))

            if rec.state not in ['draft', 'cancel']:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sales order line which is %s !') %(rec.state,))
        return super(sale_order_line, self).unlink(cr, uid, ids, context=context)


    def invoice_line_create(self, cr, uid, ids, context={}):
        create_ids = super(sale_order_line, self).invoice_line_create(cr, uid, ids, context)
        order_line_sale_brws = self.browse(cr, uid, ids)
        for line_sale in order_line_sale_brws: #lineas de la orden de venta
            # se cargan aqui para ir reflejando updates (write)
            invoice_line_brws = self.pool.get('account.invoice.line').browse(cr, uid, create_ids)
            can_write = True
            for line_invoice in invoice_line_brws: #lineas de la factura
                if can_write and line_sale.prod_lot_id.id and line_sale.product_id==line_invoice.product_id and \
                   line_sale.product_uom_qty==line_invoice.quantity and not(line_invoice.prod_lot_id):
                    #si es el mismo producto, cantidad y no se ha asignado el lote se actualiza el registro
                    #(solo 1 vez x can_write) y si tiene lote (line_sale.prod_lot_id.id)
                    upd_data = {'prod_lot_id':line_sale.prod_lot_id.id,'pieces':line_sale.pieces,'track_outgoing':line_sale.track_outgoing}
                    self.pool.get('account.invoice.line').write(cr, uid, line_invoice.id, upd_data)
                    can_write = False

        return create_ids


    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,uom=False, qty_uos=0, uos=False, name='', partner_id=False,lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False):

        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,uom, qty_uos, uos, name, partner_id,lang, update_tax, date_order, packaging, fiscal_position, flag)
        if product:
            product_obj = self.pool.get('product.product')
            produc_brw = product_obj.browse(cr,uid,product)
            res['value']['track_outgoing']=produc_brw.track_outgoing
        else:
            res['value']['track_outgoing']= False

        return res

    def warning_on_prod_lot_id_used(self, cr, uid, ids, prod_lot_id):
        res = {}
        used_lot_ids = self.search(cr, uid, [('prod_lot_id', '=', prod_lot_id),
            ('state', '!=', 'cancel')])  #, ('id','not in', ids)
        if used_lot_ids:
            used_lots = self.browse(cr, uid, used_lot_ids, context={})
            orders = '\n\t'.join(['%s - %s' % (x.order_id.name, x.order_id.user_id.name) for x in used_lots])
            res.update({'warning':
                {'title': 'Warning',
                 'message': 'Lot: %s used in order(s):\n\t%s'
                 % (used_lots[0].prod_lot_id.name, orders)}})
        return res

    def on_change_qty(self, cr, uid, ids, partner, pricelist, id_lot, uom_qty,
                      pieces_qty, context=None):
        context= context or {}
        res = {}
        product_uom_obj = self.pool.get('product.uom')
        spl_obj = self.pool.get('stock.production.lot')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if id_lot:
            spl_brw = spl_obj.browse(cr, uid, id_lot)
            res = self.product_id_change(cr, uid, ids, pricelist, spl_brw.product_id.id, qty=uom_qty,
                                         uom=False, qty_uos=0, uos=False, name='', partner_id=partner,
                                         lang=False, update_tax=True, date_order=False, packaging=False,
                                         fiscal_position=False, flag=False)
            if spl_brw.product_id.stock_driver in ('tile','slab','block'):
                area = product_uom_obj._compute_area(cr, uid, spl_brw.product_id.stock_driver, pieces_qty, spl_brw.length, spl_brw.heigth, spl_brw.width)
                if pieces_qty == 0:
                    pieces_max = product_uom_obj._compute_pieces2(cr,uid,spl_brw.product_id.stock_driver,spl_brw.virtual,spl_brw.length,spl_brw.heigth,spl_brw.width)
                    res['value'].update({'pieces': pieces_max,
                                         'product_uom_qty': spl_brw.virtual,
                                         'product_id': spl_brw.product_id and spl_brw.product_id.id,
                                         'product_uom': spl_brw.product_id.uom_id and spl_brw.product_id.uom_id.id,
                                         'name': spl_brw.product_id and spl_brw.product_id.name})
                else:
                    res['value'].update({'pieces': pieces_qty,
                                         'product_uom_qty': area,
                                         'product_id': spl_brw.product_id and spl_brw.product_id.id,
                                         'product_uom': spl_brw.product_id.uom_id and spl_brw.product_id.uom_id.id,
                                         'name': spl_brw.product_id and spl_brw.product_id.name})
                if area > spl_brw.virtual:
                    raise osv.except_osv(_('Processing Error'),
                                         _('The quantity is not available'))
                if spl_brw.product_id.stock_driver == 'block':
                    res['value'].update({'pieces': 1})
                res.update(self.warning_on_prod_lot_id_used(cr, uid, ids,
                                                            id_lot))
        return res

    # TODO product.procudt or product.template
    _inherit = 'sale.order.line'

    _columns = {'product_uom_qty': fields.float('Quantity',
                digits_compute=dp.get_precision('Product UoM')),
                'prod_lot_id': fields.many2one('stock.production.lot',
                                               'Production lot',
                                               ondelete='restrict'),
                'pieces': fields.integer('Pieces', require=True),
                'track_outgoing': fields.boolean('Track Outgoing Lot')}

    # TODO agregar validacion para requerir el nro de lote (track_outgoing)

sale_order_line()

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from report import report_sxw
from tools.translate import _
from osv import osv


class picking(report_sxw. rml_parse):
    def __init__(self, cr, uid, name, context):
        super(picking, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_address': self._get_address,
            'get_location': self._get_location,
            'get_weight': self._get_weight,
            'get_tracking_list': self._get_tracking_list,
            'get_tracking_totals': self._get_tracking_totals,
            'get_sel_str': self._get_sel_str,
            'get_title': self._get_title,
            'get_lines': self._get_lines,
            'get_summary': self._get_summary,
        })

    def _get_weight(self, move_lines):
        total = 0.0
        trackings = []
        for move in move_lines:
            total += move.product_qty * move.product_id.weight
            if move.tracking_id and move.tracking_id not in trackings:
                trackings.append(move.tracking_id)
        #~ import pdb;pdb.set_trace()
        total2 = 0.0
        for t in trackings:
            total2 += t.weight_net
        return round(total2 or total, 1)

    def _get_address(self, address):
        """This address must be a res.partner.address instance"""
        return self.pool.get('res.partner').\
            get_partner_address(self.cr, self.uid, address)

    def _get_location(self, orig, dest, type):
        if type == 'in':
            return dest
        elif type == 'internal':
            return '%s\n%s' % (orig, dest)
        else:
            return orig

    def _get_tracking_list(self, obj):
        packs = {}
        track_name = ''
        decimal_point = ','
        total_keys = ('lots', 'pieces', 'qty', 'weight', 'weight_net')
        for item in obj.move_lines:
            if not item.tracking_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('You most indicate a track package for all lots (%s)') %
                    item.prodlot_id.name)
            track_name = item.tracking_id.name
            if track_name not in packs:
                product = item.product_id
                data = {'name': track_name,
                        'id': item.tracking_id.id,
                        'product': product.name,
                        'material_id': product.material_id.name,
                        'country_id': product.origin_country_id.name,
                        'layout_id': product.layout_id.name,
                        'finish_id': product.finish_id.name,
                        'thickness': product.thickness,
                        'product_id': product.id,
                        'weight_net': item.tracking_id.weight_net,
                        'image': item.tracking_id.image or (),
                        'lots': [],
                        'totals': {'lots': 0,
                                   'pieces': 0,
                                   'qty': 0,
                                   'uom': item.product_uom.name,
                                   'weight': 0,
                                   'weight_net': 0,
                                   },
                        }
                packs.update({item.tracking_id.name: data})
            if item.product_id.id != packs[track_name]['product_id']:
                packs[track_name].update({
                    'product': _('MIXED/VARIADO'),
                    'material_id': '',
                    'country_id': '',
                    'layout_id': '',
                    'finish_id': '',
                    'thickness': '',
                    'product_id': 0,
                    })
                '''
                #~ raise osv.except_osv(
                    #~ _('Error!'),
                    #~ _('Can\'t mix diferent products in a single track ' +
                      #~ 'package (%s)') % (track_name))
                '''
            size = '%.3f x %.3f' % (item.prodlot_id.length,
                                    item.prodlot_id.heigth)
            lot = {'num': len(packs[track_name]['lots']) + 1,
                   'product': item.prodlot_id.product_id.name,
                   'name': item.prodlot_id.name,
                   'size': size.replace('.', decimal_point),
                   'pieces': item.pieces_qty,
                   'qty': item.product_qty,
                   'uom': item.product_uom.name,
                   'weight': item.product_id.weight * item.product_qty,
                   'weight_net': item.product_id.weight_net * item.product_qty,
                   }
            packs[track_name]['lots'].append(lot)
            for key in total_keys:
                packs[track_name]['totals'][key] += lot.get(key, 1)
            packs[track_name]['lots_list'] = ', '.join([
                '%s (%s)' % (x['name'], x['size'])
                for x in packs[track_name]['lots']])
        return packs.values()

    def _get_tracking_totals(self, obj):
        totals = {'pieces': 0,
                  'qty': 0,
                  'weight': 0,
                  'weight_net': 0,
                  }
        uom = ''
        for item in obj.move_lines:
            if not uom:
                uom = item.product_uom.name
            lot = {'pieces': item.pieces_qty,
                   'qty': item.product_qty,
                   'weight': item.product_id.weight * item.product_qty,
                   'weight_net': item.product_id.weight_net * item.product_qty,
                   }
            for key in totals.keys():
                totals[key] += lot.get(key, 0)
        totals.update({'uom': uom})
        return [totals]

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'assigned': _('Available'),
                            'draft': _('Draft'),
                            'auto': _('Waiting'),
                            'confirmed': _('Confirmed'),
                            'done': _('Realizado'),
                            },
                  }
        return values[type].get(val, '')

    def _get_title(self, obj):
        if obj.type == 'out':
            if obj.state == 'done':
                title = _('Out Order')
            else:
                title = _('Packing list')
        elif obj.type == 'in':
            title = _('Reception')
        elif obj.type == 'internal':
            title = _('Internal picking List')
        return title

    def _get_lines(self, obj):
        lines = []
        for item in obj.move_lines:
            location = self._get_location(item.location_id.name,
                                          item.location_dest_id.name,
                                          obj.type)
            data = {
                'product_name': item.product_id.name,
                'prodlot_name': item.prodlot_id.full_name,
                'location': location,
                'product_qty': item.product_qty,
                'product_uom': item.product_uom.name,
                'pieces_qty': item.pieces_qty,
                'order': '%s %s' % (location,
                                       item.prodlot_id.full_name),
                }
            lines.append(data)
        return sorted(lines, key=lambda k: k['order'])

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1,fld_2,...')), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]


report_sxw.report_sxw('report.stock.picking.list.tcv',
                      'stock.picking',
                      'addons/tcv_stock/report/picking.rml',
                      parser=picking)

report_sxw.report_sxw('report.stock.picking.list.tcv.export',
                      'stock.picking',
                      'addons/tcv_stock/report/picking_export.rml',
                      parser=picking)

report_sxw.report_sxw('report.stock.picking.list.tcv.export2',
                      'stock.picking',
                      'addons/tcv_stock/report/picking_export2.rml',
                      parser=picking)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

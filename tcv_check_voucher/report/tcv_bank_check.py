# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import pooler
from report.interface import report_rml
from report.report_sxw import rml_parse
from tools import to_xml
import tools
import numero_a_texto2 as nat
from textwrap import wrap
from osv import osv
from tools.translate import _


local_data = {}

def _int_2_rml(i):
    return '%d' % i


#~ def _amount_2_rml(f):
    #~ return '%.2f' % tools.formatLang(f,digits=2)


def _str_2_rml(s):
    return to_xml(tools.ustr(s or ''))


def _amount_text(amount=0):
    if not amount:
        return []
    lines = wrap(nat.Numero_a_Texto(amount).ljust(65), 64)
    lines.append('')
    return lines


def _get_city(partner=None):
    if not partner:
        return 'N/D'
    inv_addrs = [addr for addr in partner.address
                 if addr.type == 'invoice']
    if inv_addrs:
        return inv_addrs[0].city.upper()
    return 'N/D'


def _get_date(date=''):
    meses = {'01': 'ENERO', '02': 'FEBRERO', '03': 'MARZO',
             '04': 'ABRIL', '05': 'MAYO', '06': 'JUNIO',
             '07': 'JULIO', '08': 'AGOSTO', '09': 'SEPTIEMBRE',
             '10': 'OCTUBRE', '11': 'NOVIEMBRE', '12': 'DICIEMBRE'}
    fch = date.split('-')
    return ('%s DE %s' % (fch[2], meses[fch[1]]), fch[0])


def _get_type_doc(type=''):
    if type == 'normal':
        return 'Normal'
    elif type == 'advance':
        return 'Anticipo'
    elif type == 'other':
        return 'Otro'
    elif type == 'check':
        return 'Cheque'
    elif type == 'cash':
        return 'Efectivo'
    elif type == 'transfer':
        return 'Transferencia'
    else:
        return ''


def _drawString(pos, key):
    return '''
                  <drawString x="%smm"  y="%smm">%s</drawString>\n''' % \
            (pos[0], pos[1], local_data[key])


def _td_1(style, key, bold=False):
    sbold = ('<b>','</b>') if bold else ('','')
    return '''
                  <td> <para style="%s">%s%s%s</para> </td>\n''' % \
           (style, sbold[0], local_data[key], sbold[1])


def _td_2(style, title, key, bold=False):
    sbold = ('<b>','</b>') if bold else ('','')
    return '''
                  <td> <para style="CELL_LABEL">%s:</para>
                       <para style="%s">%s%s%s</para></td>\n''' % \
           (_str_2_rml(title), style, sbold[0], local_data[key], sbold[1])


class tcv_check_voucher_report(report_rml):

    def _rml_get_check_pos(self, cr, uid, ids, o, context):
        obj_pos = pooler.get_pool(cr.dbname).get('tcv.check.template.users')
        pos_id = obj_pos.search(cr, uid, [('user_id', '=', uid),
                ('bank_acc_id', '=', o.check_id.bank_acc_id.id)])
        if not pos_id:
            raise osv.except_osv(_('Error!'), _('You must indicate a ' +\
                    'template for this report'))
        pos_data = obj_pos.browse(cr, uid, pos_id[0], context=context)
        pos = {}
        for item in pos_data.template_id.line_ids:
            pos.update({item.name: [item.x,item.y]})
        delta = pos.pop('delta')
        for k in pos:
            pos.update({k: (pos[k][0] + delta[0],
                            pos[k][1] + delta[1])})
        return pos

    def _rml_parse_data(self, cr, uid, ids, o, context):
        global local_data
        str_lines = _amount_text(o.amount) or ['', '']
        str_date = _get_date(o.date)
        parser = rml_parse(cr, uid, 'parser')

        if o.voucher_type != 'other':
            title = {'sale': 'Sale',
                     'purchase': 'Purchase',
                     'payment': 'Comprobante de pago',
                     'receipt': 'Comprobante de cobro',}
        else:
            title = {'sale': 'Sale',
                     'purchase': 'Purchase',
                     'payment': 'Comprobante de egreso',
                     'receipt': 'Comprobante de ingreso',}
        user_title = {'sale': 'Sale',
                      'purchase': 'Purchase',
                      'payment': 'Pagador',
                      'receipt': 'Cobrador',}

        data = {'voucher': o,
                'amount': parser.formatLang(o.amount, digits=2),
                'beneficiary': _str_2_rml(o.beneficiary),
                'nat_str': _str_2_rml(' '.join(str_lines).strip()),
                'nat_line_1': _str_2_rml(str_lines[0]),
                'nat_line_2': _str_2_rml(str_lines[1]),
                'str_date': _str_2_rml(_get_date(o.date)),
                'city_date': _str_2_rml('%s, %s' % \
                        (_get_city(o.company_id.partner_id), str_date[0])),
                'date_year': _str_2_rml(str_date[1]),
                'restricted': 'NO ENDOSABLE',
                'comany_name': _str_2_rml('%s (%s)' % \
                        (o.company_id.partner_id.name,
                         o.company_id.partner_id.str_rif)),
                'main_title': _str_2_rml(title[o.type]),
                'nbr_title': _str_2_rml('Nº'),
                'number': _str_2_rml(o.number),
                'date': parser.formatLang(o.date, date='True'),
                'reference': _str_2_rml(o.reference),
                'partner': _str_2_rml('%s (%s)' % (o.partner_id.name, o.partner_id.str_rif or 'S/R')),
                'name': _str_2_rml(o.name),
                'payment_doc': _str_2_rml(_get_type_doc(o.payment_doc)),
                'voucher_type': _str_2_rml(_get_type_doc(o.voucher_type)),
                'period': _str_2_rml(o.period_id.name),
                'journal': _str_2_rml(o.journal_id.name),
                'bank_name': _str_2_rml(o.check_id and o.check_id.bank_acc_id.bank_id.name),
                'bank_acc_name': _str_2_rml(o.check_id and o.check_id.bank_acc_id.name),
                'check_name': o.check_id and o.check_id.full_name,
                'user_title': _str_2_rml(user_title[o.type]),
                'user_name': _str_2_rml(o.check_id and o.check_id.user_id and o.check_id.user_id.name or
                                        o.user_id and o.user_id.name),
                }
        lst = []
        for l in o.line_ids:
            factor = 1 if l.type == 'dr' else -1
            lst.append((
                    _str_2_rml('%s (%s)' % (l.name, l.move_line_id and
                                            l.move_line_id.invoice and
                                            l.move_line_id.invoice.supplier_invoice_number)),
                    _str_2_rml('[%s] %s' % (l.account_id.code,
                                            l.account_id.name)),
                    parser.formatLang(l.amount_original, digits=2),
                    parser.formatLang(l.amount_unreconciled, digits=2),
                    parser.formatLang(l.amount * factor, digits=2)
                    ))
        data.update({'line_ids': lst})
        lst = []
        if o.move_ids:
            for l in o.move_ids:
                lst.append((
                        _str_2_rml(l.account_id.code),
                        _str_2_rml(l.account_id.name),
                        parser.formatLang(l.debit, digits=2),
                        parser.formatLang(l.credit, digits=2),
                        _str_2_rml(l.reconcile_id.name)
                        ))
                acc_move = {'move': _str_2_rml(l.move_id.name),
                            'ref': _str_2_rml(l.move_id.ref),
                            'period': _str_2_rml(l.move_id.period_id.name),
                            'date': parser.formatLang(l.move_id.date, date='True'),
                            'state': _str_2_rml(l.move_id.state),
                            }
            data.update({'move_ids': lst,
                         'acc_move': acc_move})
        local_data = data
        return data

    def _table_header(self,data):
        res = '''
        <blockTable colWidths="196mm" style="TABLA_HEADER2">
            <tr>\n''' +\
              _td_1('TITLE2','comany_name', True) +\
            '''
            </tr>
        </blockTable>
        <blockTable colWidths="146mm,10mm,40mm" style="TABLA_HEADER2">
            <tr>\n''' +\
              _td_1('TITLE3','main_title', True) +\
              _td_1('TITLE6','nbr_title') +\
              _td_1('TITLE6R','number', True) +\
            '''
            </tr>
        </blockTable>
        <spacer length="2mm" />
        <blockTable colWidths="22mm,28mm,70mm,76mm" style="TABLA_FOOTER">
            <tr>\n''' +\
              _td_2('CENTRO7','Fecha', 'date', True) +\
              _td_2('CENTRO7','Referencia', 'reference', True) +\
              _td_2('LEFT7','Empresa', 'partner', True) +\
              _td_2('LEFT7','Memoria', 'name', True) +\
            '''
            </tr>
            <tr>\n''' +\
              _td_2('CENTRO7','Tipo', 'voucher_type', True) +\
              _td_2('CENTRO7','Forma de pago', 'payment_doc', True) +\
              _td_2('LEFT7','Diario', 'journal', True) +\
              _td_2('LEFT7',data['user_title'], 'user_name', True) +\
            '''
            </tr>
        </blockTable>\n'''
        if data['payment_doc'] == 'Cheque':
            res += '''
        <blockTable colWidths="44mm,40mm,65mm,20mm,27mm" style="TABLA_FOOTER">\n<tr>''' +\
              _td_2('LEFT7','Banco', 'bank_name', True) +\
              _td_2('LEFT7','Cuenta', 'bank_acc_name', True) +\
              _td_2('LEFT7','Beneficiario', 'beneficiary', True) +\
              _td_2('CENTRO7','Cheque', 'check_name', True) +\
              _td_2('RIGHT7','Monto', 'amount', True) +\
            '''
            </tr>
        </blockTable>/n'''
        else:
            res += '''
        <blockTable colWidths="169mm,27mm" style="TABLA_FOOTER">
            <tr>''' +\
              _td_2('LEFT7','Monto en letras', 'nat_str', True) +\
              _td_2('RIGHT7','Monto', 'amount', True) +\
            '''
            </tr>
        </blockTable>\n'''
        return res

    def _table_footer(self):
        return '''
        <place x="10mm" y="10mm" width="196mm" height="13mm">
          <blockTable colWidths="49mm,49mm,49mm,49mm" style="TABLA_FOOTER">
            <tr>
              <td> <para style="LEFT7">Hecho:</para>
                   <para style="LEFT7"></para></td>
              <td> <para style="LEFT7">Revisado:</para>
                   <para style="LEFT7"></para></td>
              <td> <para style="LEFT7">Aprobado:</para>
                   <para style="LEFT7"></para></td>
              <td> <para style="LEFT7">Recibido:</para>
                   <para style="TITLE2">_____________________</para>
                   <para style="LEFT7">CI:</para></td>
            </tr>
          </blockTable>
        </place>
'''

    def _pageTemplate_1a(self, pos, data):
        """
        All measures are in mm from left bottom corner (check)
        Delta is measure from page (sheet)
        pos = {'amount':[149,67],
               'beneficiary':[30,53],
               'nat_line_1':[30,47],
               'nat_line_2':[10,41],
               'city_date':[10,35],
               'date_year':[10,35],
               'restricted':[115,28],
               'delta':[0,200],
                }
        """

        template = '''
    <pageTemplate id="first_template">
        <pageGraphics>
            <setFont name="Helvetica-Bold" size="12"/>'''+ \
            _drawString(pos['amount'], 'amount') +\
            '''
            <setFont name="Helvetica" size="11"/>''' +\
            _drawString(pos['beneficiary'], 'beneficiary') +\
            _drawString(pos['nat_line_1'], 'nat_line_1') +\
            _drawString(pos['nat_line_2'], 'nat_line_2') +\
            _drawString(pos['city_date'], 'city_date') +\
            _drawString(pos['date_year'], 'date_year') +\
            _drawString(pos['restricted'], 'restricted') +\
      '''
          <place x="10mm" y="145mm" width="196mm" height="50mm">''' +\
            self._table_header(data) +\
      '''
          </place>\n''' +\
        self._table_footer() +\
      '''
      </pageGraphics>
      <frame id="first" x1="10mm" y1="26mm" width="196mm" height="126mm"/>
    </pageTemplate>\n'''
        return template

    def _pageTemplate_1b(self, data):
        template = '''
    <pageTemplate id="first_template">
        <pageGraphics>
          <place x="10mm" y="215mm" width="196mm" height="50mm">''' + \
            self._table_header(data) + \
      '''
          </place>''' +\
            self._table_footer() +\
      '''
      </pageGraphics>
      <frame id="first" x1="10mm" y1="26mm" width="196mm" height="188mm"/>
    </pageTemplate>\n'''
        return template

    def _pageTemplate_2(self, data):
        template = '''
    <pageTemplate id="template_2">
        <pageGraphics>
          <place x="10mm" y="215mm" width="196mm" height="50mm">\n''' % \
            ()
        template += self._table_header(data)
        template += '''
        </place>
        <setFont name="Helvetica" size="7.0"/>
        <drawString x="137mm" y="253mm">%s</drawString>
        <drawCentredString x="108mm" y="8mm">%s <pageNumber/></drawCentredString>
      </pageGraphics>
      <frame id="next_frame" x1="10mm" y1="14mm" width="196mm" height="205mm"/>
    </pageTemplate>\n''' % (_str_2_rml('Continuación...'),
                            _str_2_rml('Página'))
        return template

    def _stylesheet(self):
        return '''
  <stylesheet>
    <blockTableStyle id="TABLA_HEADER2">
      <blockAlignment value="LEFT" />
      <blockValign value="CENTER" />
      <lineStyle kind="GRID" colorName="#000000" start="0,0" stop="-1,-1" />
      <blockBackground kind="GRID" colorName="khaki" start="0,0" stop="-1,-1" />
    </blockTableStyle>
    <blockTableStyle id="TABLA_HEADER">
      <lineStyle kind="GRID" colorName="#000000" start="0,0" stop="-1,-1" />
      <blockBackground kind="GRID" colorName="khaki" start="0,0" stop="-1,-1" />
      <blockSpan start="1,0" stop="2,0" />
      <blockSpan start="0,1" stop="1,1" />
      <blockSpan start="2,1" stop="-1,1" />
      <blockSpan start="0,-1" stop="-1,-1" />
      <blockValign value="CENTER" />
    </blockTableStyle>
    <blockTableStyle id="TABLA_BODY">
      <blockAlignment value="LEFT" />
      <blockValign value="CENTER" />
      <lineStyle kind="GRID" colorName="darkgrey" start="0,0" stop="-1,-1" />
      <blockBackground kind="GRID" colorName="white" start="0,0" stop="-1,-1" />
    </blockTableStyle>
    <blockTableStyle id="TABLA_FOOTER">
      <blockAlignment value="LEFT" />
      <blockValign value="TOP" />
      <lineStyle kind="GRID" colorName="darkgrey" start="0,0" stop="-1,-1" />
      <blockBackground kind="GRID" colorName="white" start="0,0" stop="-1,-1" />
    </blockTableStyle>
    <initialize>
      <paraStyle name="all" alignment="justify" />
    </initialize>
    <paraStyle name="DERECHA" alignment="RIGHT" fontName="Helvetica" fontSize="8.0" leading="9" spaceBefore="0" textColor="black" />
    <paraStyle name="IZQUIERDA" alignment="LEFT" fontName="Helvetica" fontSize="8.0" leading="9" spaceBefore="0" textColor="black" />
    <paraStyle name="CENTRO" alignment="CENTER" fontName="Helvetica" fontSize="8.0" leading="8" spaceBefore="0" textColor="black" />
    <paraStyle name="DERECHAN" alignment="RIGHT" fontName="Helvetica-Bold" fontSize="8.0" leading="9" spaceBefore="0" textColor="black" />
    <paraStyle name="IZQUIERDAN" alignment="LEFT" fontName="Helvetica-Bold" fontSize="8.0" leading="9" spaceBefore="0" textColor="black" />
    <paraStyle name="CENTRON" alignment="CENTER" fontName="Helvetica-Bold" fontSize="8.0" leading="8" spaceBefore="0" textColor="black" />
    <paraStyle name="CENTRO7" alignment="CENTER" fontName="Helvetica" fontSize="7.0" leading="7" spaceBefore="0" textColor="black" />
    <paraStyle name="CENTRO7N" alignment="CENTER" fontName="Helvetica-Bold" fontSize="7.0" leading="7" spaceBefore="0" textColor="black" />
    <paraStyle name="LEFT7" alignment="LEFT" fontName="Helvetica" fontSize="7.0" leading="7" spaceBefore="0" textColor="black" />
    <paraStyle name="CELL_LABEL" alignment="LEFT" fontName="Helvetica" fontSize="7.0" leading="8" spaceBefore="0" textColor="black" />
    <paraStyle name="RIGHT7" alignment="RIGHT" fontName="Helvetica" fontSize="7.0" leading="7" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE" alignment="CENTER" fontName="Helvetica" fontSize="20.0" leading="20" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE2" alignment="LEFT" fontName="Helvetica" fontSize="12.0" leading="15" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE3" alignment="LEFT" fontName="Helvetica" fontSize="10.0" leading="10" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE4" alignment="LEFT" fontName="Helvetica" fontSize="20.0" leading="20" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE5" alignment="LEFT" fontName="Helvetica" fontSize="15.0" leading="15" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE6" alignment="LEFT" fontName="Helvetica" fontSize="9.0" leading="9" spaceBefore="0" textColor="black" />
    <paraStyle name="TITLE6R" alignment="RIGHT" fontName="Helvetica" fontSize="9.0" leading="9" spaceBefore="0" textColor="black" />
    <blockTableStyle id="TITLE">
      <lineStyle kind="GRID" colorName="black" start="0,0" stop="-1,-1" thickness="0.5" />
      <blockValign value="TOP" />
    </blockTableStyle>
  </stylesheet>\n'''

    def _content_blockTable(self, titles, data):
        block = '''
        <blockTable colWidths="196mm" style="TABLA_HEADER2">
          <tr>
            <td> <para style="CENTRON">%s</para> </td>
          </tr>
        </blockTable>
        <spacer length="2mm" />\n
        <blockTable colWidths="25mm,96mm,25mm,25mm,25mm" style="TABLA_FOOTER" repeatRows="1">
          <tr>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
          </tr>\n''' % titles
        for l in data:
            block += '''
              <tr>
                <td> <para style="CENTRO7">%s</para></td>
                <td> <para style="LEFT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
              </tr>\n''' % l
        block += '''            </blockTable>'''
        return block

    def _content_blockTable_move(self, titles, data, move):
        block = '''
        <blockTable colWidths="196mm" style="TABLA_HEADER2">
          <tr>
            <td> <para style="CENTRON">%s</para> </td>
          </tr>
        </blockTable>\n''' % titles[0]
        acc_move = '''
          <spacer length="2mm" />
          <blockTable colWidths="35mm,76mm,35mm,25mm,25mm" style="TABLA_BODY" repeatRows="1">
            <tr>
              <td> <para style="CELL_LABEL">Number:</para>
                 <para style="CENTRON">%s</para></td>
              <td> <para style="CELL_LABEL">Ref:</para>
                 <para style="CENTRON">%s</para></td>
              <td> <para style="CELL_LABEL">Period:</para>
                 <para style="CENTRON">%s</para></td>
              <td> <para style="CELL_LABEL">Date:</para>
                 <para style="CENTRON">%s</para></td>
              <td> <para style="CELL_LABEL">State:</para>
                 <para style="CENTRON">%s</para></td>
            </tr>
          </blockTable>\n''' % move
        lines = '''
        <spacer length="2mm" />

        <blockTable colWidths="25mm,96mm,25mm,25mm,25mm" style="TABLA_FOOTER" repeatRows="1">
          <tr>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
            <td> <para style="CENTRO7N">%s</para></td>
          </tr>\n''' % titles[1:]
        for l in data:
            lines += '''
              <tr>
                <td> <para style="CENTRO7">%s</para></td>
                <td> <para style="LEFT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
                <td> <para style="RIGHT7">%s</para></td>
              </tr>\n''' % l
        lines += '''            </blockTable>'''
        return block + acc_move + lines

    def _story(self,data):
        sty = '''  <story>\n'''
        sty += '''  <setNextTemplate name="template_2"></setNextTemplate>\n'''
        if data.get('line_ids'):
            sty += self._content_blockTable(('Facturas y otras transacciones',
                                      'Apunte (Factura)',
                                      'Cuenta',
                                      'Importe original',
                                      'Saldo',
                                      'Importe'),
                                      data['line_ids'])
            sty += '''        <spacer length="2mm"/>\n'''
        if data.get('acc_move'):
            sty += self._content_blockTable_move(('Apuntes contables',
                                      _str_2_rml('Código'),
                                      'Cuenta',
                                      'Debe',
                                      'Haber',
                                      _str_2_rml('Conciliación')),
                                      data['move_ids'],
                                      (data['acc_move']['move'],
                                       data['acc_move']['ref'],
                                       data['acc_move']['period'],
                                       data['acc_move']['date'],
                                       _(data['acc_move']['state'].capitalize()),
                                      )
                                     )
        sty += '''  </story>\n'''
        return sty

    def create(self, cr, uid, ids, datas, context):
        #~ xml = self.create_xml(cr, uid, ids, datas, context)
        #~ print xml
        #~ xml = tools.ustr(xml).encode('utf8')
        #~ report_type = datas.get('report_type', 'pdf')
        #~ if report_type == 'raw':
            #~ return (xml,report_type)
        #~ rml = self.create_rml(cr, xml, uid, context)
        #~ pool = pooler.get_pool(cr.dbname)
        #~ ir_actions_report_xml_obj = pool.get('ir.actions.report.xml')
        #~ report_xml_ids = ir_actions_report_xml_obj.search(cr, uid, [('report_name', '=', self.name[7:])], context=context)
        #~ self.title = report_xml_ids and ir_actions_report_xml_obj.browse(cr,uid,report_xml_ids)[0].name or 'OpenERP Report'
        #~ create_doc = self.generators[report_type]
        #~ pdf = create_doc(rml, title=self.title)

        obj_vou = pooler.get_pool(cr.dbname).get('account.voucher')
        o = obj_vou.browse(cr, uid, datas['id'], context=context)
        data = self._rml_parse_data(cr, uid, ids, o, context)

        rml ='''<?xml version="1.0"?>
<document filename="tcv_account_voucher.pdf">
<template pageSize="(8.5in,11in)" title="tcv account voucher" author="Juan Marquez" allowSplitting="20" showBoundary='0'>'''
        if data['payment_doc'] == 'Cheque':
            pos = self._rml_get_check_pos(cr, uid, ids, o, context)
            rml += self._pageTemplate_1a(pos, data)
        else:
            rml += self._pageTemplate_1b(data)
        rml += self._pageTemplate_2(data)
        rml += '''</template>'''
        rml += self._stylesheet()
        rml += self._story(data)
        rml += '''</document>'''
        report_type = datas.get('report_type', 'pdf')
        create_doc = self.generators[report_type]
        pdf = create_doc(rml, title=self.title)
        return (pdf, report_type)

tcv_check_voucher_report('report.tcv_check_voucher_report', 'account.voucher','','')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

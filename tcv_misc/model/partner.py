# -*- encoding: utf-8 -*-
##############################################################################
#
#~ Incorpora el campo rif como campo funcional para tener acceso fácil al
#~ rif en venezuela y no tener que estar separandolo cada vez
#
##############################################################################
from osv import fields, osv
from tools.translate import _
import time
import requests
import json


class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _get_partner_rif(self, cr, uid, ids, name, arg, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        for item in self.browse(cr, uid, ids, context={}):
            vat = item.vat
            if vat and vat[:2] == 'VE' and len(vat) == 12:
                res[item.id] = {
                    'rif': vat[2:],
                    'str_rif': '-'.join((vat[2], vat[3:11], vat[11]))}
            else:
                vat = vat[2:] if vat and len(vat) > 2 else vat
                res[item.id] = {'rif': vat, 'str_rif': vat}
        return res

    def get_partner_address(self, cr, uid, address, addr_type='invoice',
                            context=None):
        context = context or {}
        if isinstance(address, (int, long)):
            addr = self.pool.get('res.partner.address').\
                browse(cr, uid, address, context=context)
        elif isinstance(address, list):
            addr = [addr for addr in address if addr.type == addr_type][0]
        else:
            addr = address
        if addr:
            addr_data = [addr.street or '',
                         addr.street2 or '',
                         addr.city or '',
                         addr.state_id and addr.state_id.name or '',
                         addr.country_id and addr.country_id.name if
                         addr.country_id.code != 'VE' else '',
                         addr.phone and _('Phone: %s') % addr.phone or '',
                         addr.fax and _('Fax: %s') % addr.fax or '',
                         addr.mobile and _('Mobile: %s') % addr.mobile or '',
                         addr.email and _('eMail: %s') % addr.email or '',
                         ]
            if context.get('partner_rif'):
                addr_data.append(_('RIF: %s') % context('partner_rif'))
            while '' in addr_data:
                addr_data.remove('')
            return ', '.join(addr_data) + '.'
        return ''

    def _find_accounting_partner(self, partner):
        '''
        Find the partner for which the accounting entries will be created
        '''
        # FIXME: after 7.0, to replace by function field
        # partner.commercial_partner_id
        # if the chosen partner is not a company and has a parent company,
        # use the parent for the journal entries
        # because you want to invoice 'Agrolait, accounting department' but
        # the journal items are for 'Agrolait'
        return partner

    _columns = {
        'rif': fields.function(_get_partner_rif, method=True, type="char",
                               string='RIF', multi='all'),
        'str_rif': fields.function(_get_partner_rif, method=True,
                                   type="char", string='RIF', multi='all'),
        'property_stock_purchase': fields.property(
            'stock.location', type='many2one',
            relation='stock.location', string="Supplier Location",
            method=True, view_load=True,
            help="This stock location will be used, instead of the default " +
            "one, as the destination location for goods you receive from " +
            "the current supplier"),
        'rupdae': fields.char(
            'Rupdae', size=32, required=False, readonly=False,
            help="Registro Único de Personas que Desarrollan Actividades " +
            "Económicas. Antes de poder consultar el Rupdae debe verificar" +
            "el RIF ante el SENIAT"),
        }

    def get_rupdae_data(self, cr, uid, rif):
        """
        This scrip get data from rupdae.superintendenciadepreciosjustos.gob.ve
        using
        http://stackoverflow.com/questions/11322430/
            python-how-to-send-post-request
        http://stackoverflow.com/questions/20495532/
            decode-json-response-from-ajax-call
        result = json data with 2 important fields:
            validacion: True or False if data request is ok
            msg: a string with html code and data fields

        msg sample:
            <div  class="row"><div class="col-md-12">
                <h4>Rif: J123456789</h4>
                <h4>Razón Social: [[comany name]];</h4>
                <h4>Fecha de Inscripción: 09-03-2015</h4>
                <h4>Certificado de Inscripción N°:[[ 32 char]]</h4>
            </div></div><hr>

        """
        url_rupdae = "http://rupdae.superintendenciadepreciosjustos.gob.ve" + \
            "/usuarios/validar-registro"
        res = {'valid': False}
        try:
            r = requests.post(
                url_rupdae, data={'solicitud-ajax': True, 'usuario': rif},
                timeout=3)
            if r.status_code == 200:
                json_data = json.loads(r.text)
                if json_data.get('validacion'):
                    html = json_data.get('msg', ' ' * 64)
                    #~ Parse html to get field values
                    values = [x.split(':')[1].strip().split('</h4>')[0]
                              for x in html.split('<h4>')[1:]]
                    if len(values) == 4:
                        res.update({
                            'valid': json_data.get('validacion'),
                            'rif': values[0],
                            'name': values[1][:-1],
                            'date': time.strftime(
                                '%Y-%m-%d', time.strptime(
                                    values[2], '%d-%m-%Y')),
                            'rupdae': values[3],
                            })
                    return res
        except:
            pass
        return res

    def update_rupdae(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for partner in self.browse(cr, uid, ids, context={}):
            if partner.vat and partner.vat[:2] == 'VE' and \
                    len(partner.vat) == 12:
                rupdae = self.get_rupdae_data(cr, uid, partner.rif)
                if rupdae.get('valid') and rupdae.get('rupdae'):
                    self.write(
                        cr, uid, [partner.id],
                        {'rupdae': rupdae.get('rupdae', '')},
                        context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        vals.update({'company_id': 0})
        if not vals.get('date'):
            vals.update({'date': time.strftime('%Y-%m-%d')})
        res = super(res_partner, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        vals.update({'company_id': 0})
        res = super(res_partner, self).write(cr, uid, ids, vals, context)
        return res

res_partner()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

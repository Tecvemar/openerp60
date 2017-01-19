# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-03-27
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
import decimal_precision as dp
import time
#~ import netsvc

##---------------------------------------------------------------- tcv_rrhh_ari


class tcv_rrhh_ari(osv.osv):

    _name = 'tcv.rrhh.ari'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True, select=True,
            states={'draft': [('readonly', False)]}),
        'ut_id': fields.many2one(
            'l10n.ut', 'U.T.', change_default=True, readonly=True,
            required=True, states={'draft': [('readonly', False)]},
            ondelete='restrict'),
        'narration': fields.text(
            'Notes', readonly=False),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'forms_ids': fields.one2many(
            'tcv.rrhh.ari.forms', 'ari_id', 'AR-I', readonly=True,
            states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'name': lambda *a: '/',
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_print(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        return {
            'name': _("Print AR-I"),
            'view_mode': 'tree',
            'view_id': False,
            'view_type': 'tree',
            'res_model': 'tcv.rrhh.ari.forms',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('ari_id', 'in', ids)],
            'context': {}
            }

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                        get(cr, uid, 'tcv.rrhh.ari')})
        res = super(tcv_rrhh_ari, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True

tcv_rrhh_ari()


##---------------------------------------------------------- tcv_rrhh_ari_forms


class tcv_rrhh_ari_forms(osv.osv):

    _name = 'tcv.rrhh.ari.forms'

    #~ _rec_name = 'employee_id'

    _description = ''

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s (%s)' % (item.ari_id.name,
                                         item.name,
                                         item.ari_id.date)))
        return res

    ##------------------------------------------------------- _internal methods

    def _compute_personal_tax(self, amount):
        if amount <= 0:
            tax = 0
        elif amount <= 1000:
            tax = round(amount * 0.06, 2)
        elif amount <= 1500:
            tax = round(amount * 0.09, 2) - 30
        elif amount <= 2000:
            tax = round(amount * 0.12, 2) - 75
        elif amount <= 2500:
            tax = round(amount * 0.16, 2) - 155
        elif amount <= 3000:
            tax = round(amount * 0.20, 2) - 255
        elif amount <= 4000:
            tax = round(amount * 0.24, 2) - 375
        elif amount <= 6000:
            tax = round(amount * 0.29, 2) - 575
        else:
            tax = round(amount * 0.34) - 875
        return tax

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        rebate_u = 774
        for item in self.browse(cr, uid, ids, context=context):
            ut = item.ari_id.ut_id.amount
            total = 0
            for line in item.income_ids:
                total += line.amount
            total_ut = round(total / ut, 2) if total > 0 else 0
            amount_rebate = rebate_u * ut if item.tax_rebate_u else \
                item.tax_rebate_1 + item.tax_rebate_2 + \
                item.tax_rebate_3 + item.tax_rebate_4
            rebate_ut = round(amount_rebate / ut, 2)
            base_tax = self._compute_personal_tax(total_ut - rebate_ut)
            family_disc = item.family_chrg * 10
            tax_excess = round(item.tax_excess / ut)
            tax_discount = 10 + family_disc + tax_excess
            net_tax = base_tax - tax_discount
            if net_tax < 0:
                net_tax = 0
            if net_tax:
                if item.today_salary == 0:
                    pct_tax = round((net_tax / total_ut) * 100, 2) \
                        if total_ut else 0
                else:
                    f1 = round((net_tax * ut) - item.today_tax, 2)
                    f2 = total - (
                        item.today_salary - item.today_salary_discount)
                    pct_tax = round((f1 / f2) * 100, 2)
            else:
                pct_tax = 0
            if pct_tax < 0:
                pct_tax = 0

            res[item.id] = {'amount_compute': total,
                            'amount_rebate': amount_rebate,
                            'base_tax': base_tax,
                            'tax_discount': tax_discount,
                            'net_tax': net_tax,
                            'pct_tax': pct_tax}
        return res

    def _update_family_chrg(self, cr, uid, vals, context=None):
        if vals.get('employee_id') and vals.get('family_chrg'):
            obj_emp = self.pool.get('hr.employee')
            obj_emp. write(cr, uid, vals['employee_id'],
                           {'family_chrg': vals['family_chrg']},
                           context=context)

    ##--------------------------------------------------------- function fields

    _columns = {
        'ari_id': fields.many2one(
            'tcv.rrhh.ari', 'AR-I', required=True, ondelete='cascade'),
        'employee_id': fields.many2one(
            'hr.employee', "Employee", required=True, ondelete='restrict'),
        'name': fields.related(
            'employee_id', 'name', type='char', size=64, string='Name',
            store=False, readonly=True),
        'income_ids': fields.one2many(
            'tcv.rrhh.ari.incomes', 'form_id', 'Incomes'),
        'amount_compute': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all',
            help="TOTAL QUE ESTIMA PERCIBIR"),
        'tax_rebate_u': fields.boolean(
            'Tax rebate unq.', help="USAR DESGRAVAMEN UNICO"),
        'tax_rebate_1': fields.float(
            'Tax rebate 1', digits_compute=dp.get_precision('Account'),
            help="INSTITUTOS DOCENTES POR LA EDUCACION DEL CONTRIBUYENTE " +
            "Y DESCENDIENTES NO MAYORES DE 25 AÑOS"),
        'tax_rebate_2': fields.float(
            'Tax rebate 2', digits_compute=dp.get_precision('Account'),
            help="PRIMAS DE SEGUROS DE HOSPITALIZACION, CIRUGIA Y " +
            "MATERNIDAD"),
        'tax_rebate_3': fields.float(
            'Tax rebate 3', digits_compute=dp.get_precision('Account'),
            help="SERVICIOS MEDICOS ODONTOLOGICOS Y DE HOSPITALIZACION " +
            "(INCLUYE CARGA FAMILIAR)"),
        'tax_rebate_4': fields.float(
            'Tax rebate 4', digits_compute=dp.get_precision('Account'),
            help="INTERESES PARA LA ADQUISICION DE LA VIVIENDA PRINCIPAL " +
            "O DE LO PAGADO POR ALQUILER DE LA VIVIENDA QUE LE SIRVE DE " +
            "ASIENTO PERMANENTE DEL HOGAR"),
        'tax_excess': fields.float(
            'Tax excess', digits_compute=dp.get_precision('Account'),
            help="IMPUESTOS RETENIDOS DE MAS EN AÑOS ANTERIORES"),
        'amount_rebate': fields.function(
            _compute_all, method=True, type='float', string='Total rebate',
            digits_compute=dp.get_precision('Account'), multi='all',
            help="TOTAL DESGRAVAMENES ESTIMADOS"),
        'base_tax': fields.function(
            _compute_all, method=True, type='float', string='Base tax',
            digits_compute=dp.get_precision('Account'), multi='all',
            help="IMPUESTO (ESTIMADO) A RETENER EN EL AÑO GRAVABLE"),
        'tax_discount': fields.function(
            _compute_all, method=True, type='float', string='Tax disc.',
            digits_compute=dp.get_precision('Account'), multi='all',
            help="TOTAL REBAJAS"),
        'net_tax': fields.function(
            _compute_all, method=True, type='float', string='Net tax',
            digits_compute=dp.get_precision('Account'), multi='all',
            help="IMPUESTO (ESTIMADO) A RETENER EN EL AÑO GRAVABLE"),
        'pct_tax': fields.function(
            _compute_all, method=True, type='float', string='% Tax',
            digits_compute=dp.get_precision('Account'), multi='all',
            help=" PORCENTAJE DE RETENCION DETERMINADO"),
        'family_chrg': fields.integer(
            'Family', help="CARGA FAMILIAR (VER INSTRUCTIVO) CANTIDAD"),
        'today_tax': fields.float(
            'Today tax', digits_compute=dp.get_precision('Account'),
            help="TOTAL DE IMPUESTO QUE LE HAN RETENIDO HASTA LA FECHA"),
        'today_salary': fields.float(
            'Today salary', digits_compute=dp.get_precision('Account'),
            help="TOTAL REMUNERACIONES PERCIBIDAS HASTA LA FECHA"),
        'today_salary_discount': fields.float(
            'Today salary discount',
            digits_compute=dp.get_precision('Account'),
            help="*EXONERACIONES ESPECIALES AL INGRESO"),
        #~ 'state': fields.related(
            #~ 'ari_id', 'state', type='char', size=16, string='State',
            #~ store=False, readonly=True),
        }

    _defaults = {
        'tax_rebate_u': lambda *a: True,
        }

    _sql_constraints = [
        ('tax_rebate_1_range', 'CHECK(tax_rebate_1 >= 0)',
         'The field tax_rebate_1 must be >= 0!'),
        ('tax_rebate_2_range', 'CHECK(tax_rebate_2 >= 0)',
         'The field tax_rebate_2 must be >= 0!'),
        ('tax_rebate_3_range', 'CHECK(tax_rebate_3 >= 0)',
         'The field tax_rebate_3 must be >= 0!'),
        ('tax_rebate_4_range', 'CHECK(tax_rebate_4 >= 0)',
         'The field tax_rebate_4 must be >= 0!'),
        ('tax_excess_range', 'CHECK(tax_excess >= 0)',
         'The field tax_excess must be >= 0!'),
        ('today_tax_range', 'CHECK(today_tax >= 0)',
         'The field today_tax must be >= 0!'),
        ('today_salary_range', 'CHECK(today_salary >= 0)',
         'The field today_salary must be >= 0!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_compute(self, cr, uid, ids, context=None):
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        res = super(tcv_rrhh_ari_forms, self).create(cr, uid, vals, context)
        self._update_family_chrg(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(tcv_rrhh_ari_forms, self).write(cr, uid, ids, vals,
                                                    context)
        self._update_family_chrg(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_rrhh_ari_forms()


##-------------------------------------------------------- tcv_rrhh_ari_incomes


class tcv_rrhh_ari_incomes(osv.osv):

    _name = 'tcv.rrhh.ari.incomes'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'form_id': fields.many2one(
            'tcv.rrhh.ari.forms', 'Forms', required=True, ondelete='cascade'),
        'name': fields.char(
            'Partner', size=64, required=False, readonly=False,
            help="NOMBRE DE LA EMPRESA U ORGANISMO DONDE TRABAJA"),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            help="CANTIDAD POR PERCIBIR DE LA EMPRESA U ORGANISMO"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('amount_range', 'CHECK(amount != 0)',
         'The field amount must be <> 0!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_rrhh_ari_incomes()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

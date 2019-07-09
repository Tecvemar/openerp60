# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-30
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ from datetime import datetime
#~ import netsvc
import logging
logger = logging.getLogger('server')

##--------------------------------------------------- tcv_payroll_import_profit


class tcv_payroll_import_profit(osv.osv_memory):

    _name = 'tcv.payroll.import.profit'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _exec_sql(self, cr, uid, profit_db, sql, context):
        obj_cfg = self.pool.get('tcv.profit.import.config')
        obj_cfg.get_profit_db_cursor(
            cr, uid, [profit_db.id], context=context)
        obj_cfg.exec_sql(sql)
        return obj_cfg.fetchall()

    def _clean_data_list(self, data_list, field_list):
        res = []
        for row in data_list:
            data = {}
            for key in row:
                if key in field_list:
                    data.update({key: row[key]})
            if data:
                res.append(data)
        return res

    def _import_data(self, cr, uid, obj_name, data_list, context):
        imported = 0
        obj = self.pool.get(obj_name)
        for item in data_list:
            obj_id = obj.search(cr, uid, [('code', '=', item['code'])])
            if not obj_id:
                logger.info('Profit data import (%s): %s' %
                            (obj_name, str(item)))
                obj.create(cr, uid, item, context)
                imported += 1
        return imported

    #~ Contracts

    def _get_contracts(self, cr, uid, profit_db, field_list, context=None):
        context = context or {}
        sql = '''
            select %s rtrim(co_cont) as code, rtrim(des_cont) as name,
                   'contract' as type
            from sncont
            order by co_cont
            ''' % context.get('records_limit', '')
        data_list = self._exec_sql(
            cr, uid, profit_db, sql, context=context)
        return self._clean_data_list(data_list, field_list)

    def _import_contracts(self, cr, uid, profit_db, context=None):
        data_list = self._get_contracts(
            cr, uid, profit_db, ['code', 'name', 'type'], context)
        return self._import_data(
            cr, uid, 'tcv.payroll.import.data', data_list, context)

    #~ Concepts

    def _get_concepts(self, cr, uid, profit_db, field_list, context=None):
        context = context or {}
        sql = '''
            select %s rtrim(co_conce) as code, rtrim(des_conce) as name,
                'concept' as type
            from snconcep where noenviar = 0 or tipo != 4
            order by co_conce
            ''' % context.get('records_limit', '')
        data_list = self._exec_sql(
            cr, uid, profit_db, sql, context=context)
        return self._clean_data_list(data_list, field_list)

    def _import_concepts(self, cr, uid, profit_db, context=None):
        data_list = self._get_concepts(
            cr, uid, profit_db, ['code', 'name', 'type'], context)
        return self._import_data(
            cr, uid, 'tcv.payroll.import.data', data_list, context)

    #~ Jobs

    def _get_jobs(self, cr, uid, profit_db, field_list, context=None):
        context = context or {}
        sql = '''
            select %s distinct rtrim(e.co_cargo) as code,
                   rtrim(c.des_cargo) as name
            from snemple e
            left join sncargo c on e.co_cargo = c.co_cargo
            where e.status = 'A'
            order by code, name
            ''' % context.get('records_limit', '')
        data_list = self._exec_sql(
            cr, uid, profit_db, sql, context=context)
        return self._clean_data_list(data_list, field_list)

    def _import_jobs(self, cr, uid, profit_db, context=None):
        data_list = self._get_jobs(
            cr, uid, profit_db, ['code', 'name'], context)
        return self._import_data(
            cr, uid, 'hr.job', data_list, context)

    #~ Employee

    def _get_employees(self, cr, uid, profit_db, field_list, context=None):
        context = context or {}
        sql = '''
            select %s rtrim(e.cod_emp) as code,
                   rtrim(e.nombres) as name,
                   rtrim(e.ci) as identification_id,
                   case sexo when 'M' then 'male' else 'female' end as gender,
                   rtrim(co_cargo) as job,
                   rtrim(telefono) as work_phone,
                   rtrim(direccion) as address,
                   fecha_nac as birthday,
                   rtrim(campo7) as vat,
                   case edo_civ when 'S' then 1
                                when 'C' then 2
                                when 'D' then 3
                                when 'V' then 4
                                else 0 end as marital,
                   rtrim(co_cont) as co_cont
            from snemple e
            where e.status = 'A'
            order by code
            ''' % context.get('records_limit', '')
        data_list = self._exec_sql(
            cr, uid, profit_db, sql, context=context)
        return self._clean_data_list(data_list, field_list)

    def _import_employees(self, cr, uid, profit_db, context=None):
        '''
        Create hr.employee & res.partner is necesary or if exits
        assign res.partner to hr.employee
        '''

        def _upcase(string):
            return string.decode('utf-8').upper()

        obj_pnr = self.pool.get('res.partner')
        obj_job = self.pool.get('hr.job')
        obj_emp = self.pool.get('hr.employee')
        obj_con = self.pool.get('tcv.payroll.import.data')
        job_ids = obj_job.search(cr, uid, [])
        job_brw = obj_job.browse(cr, uid, job_ids, context=context)
        jobs = {}
        country_id = self.pool.get('res.country').\
            search(cr, uid, [('code', '=', 'VE')])[0]
        category_id = self.pool.get('res.partner.category').\
            search(cr, uid, [('name', '=', 'Empleados')])[0]
        for j in job_brw:
            jobs.update({j.code: j.id})
        field_list = ['code', 'name', 'identification_id', 'gender', 'job',
                      'work_phone', 'address', 'birthday', 'vat', 'marital',
                      'co_cont']
        data_list = self._get_employees(
            cr, uid, profit_db, field_list, context)
        imported = 0
        for emp in data_list:
            emp.update({'job_id': jobs.get(emp['job'])})
            if not emp.get('vat'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate a VAT for %s') % emp['name'])
            emp['vat'] = 'VE%s' % emp['vat']
            emp['vat'] = _upcase(emp['vat'].replace('-', '').replace(' ', ''))
            partner_id = obj_pnr.search(
                cr, uid, [('vat', '=', emp['vat'])])
            if not partner_id:
                cont_id = obj_con.search(
                    cr, uid, [('code', '=', emp['co_cont']),
                              ('type', '=', 'contract')])
                cont = obj_con.browse(cr, uid, cont_id, context=context)
                if not cont or not cont[0].account_kind_rec or \
                        not cont[0].account_kind_pay:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must indicate an accounting classification for ' +
                          'the contract: %s') % emp['co_cont'])
                rpa_rec_brw = cont[0].account_kind_rec
                rpa_pay_brw = cont[0].account_kind_pay
                partner = {
                    'name': _upcase(emp['name']),
                    'ref': emp['identification_id'],
                    'lang': 'es_VE',
                    'vat': emp['vat'],
                    'address': [(0, 0, {'type': 'invoice',
                                        'name': _upcase(emp['name']),
                                        'street': _upcase(emp['address']),
                                        'phone': _upcase(emp['work_phone']),
                                        'country_id': country_id,
                                        })],
                    'customer': True,
                    'supplier': False,
                    'account_kind_rec': rpa_rec_brw.id,
                    'property_account_receivable':
                    rpa_rec_brw.property_account_partner_default.id,
                    'property_account_advance':
                    rpa_rec_brw.property_account_advance_default.id,
                    'account_kind_pay': rpa_pay_brw.id,
                    'property_account_payable':
                    rpa_pay_brw.property_account_partner_default.id,
                    'property_account_prepaid':
                    rpa_pay_brw.property_account_advance_default.id,
                    'category_id': [(4, category_id)],
                    'company_id': 0,
                    'isrl_withholding_agent': True,
                    'comment': _('Employee code: %s') % emp['code'],
                    'wh_iva_rate': 100.0,
                    }
                try:
                    logger.info('Profit data import (%s): %s' %
                                ('res.partner', str(partner)))
                    partner_id = obj_pnr.create(cr, uid, partner, context)
                except Exception, e:
                    logger.info(
                        'Can\'t create partner: [%s] %s\n%s' %
                        (emp['vat'], _upcase(emp['name']), str(e)))

                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t create partner: [%s] %s\nData:\n%s\n%s\n' +
                          'Check the contract\'s accounting clasification!') %
                        (emp['vat'], _upcase(emp['name']), str(partner),
                         str(e)))
            else:
                partner_id = partner_id[0]
            pnr_brw = obj_pnr.browse(
                cr, uid, partner_id, context=context)
            address_home = [addr for addr in pnr_brw.address
                            if addr.type == 'invoice'][0]
            emp.update({'address_home_id': address_home.id})

            emp_id = obj_emp.search(cr, uid, [('code', '=', emp['code'])])
            if not emp_id:
                logger.info('Profit data import (%s): %s' %
                            ('hr.employee', str(emp)))
                emp_id = obj_emp.create(cr, uid, emp, context)
                imported += 1
            else:
                emp_brw = obj_emp.browse(cr, uid, emp_id, context=context)[0]
                emp_upd = {}
                if not emp_brw.address_home_id or \
                        emp_brw.address_home_id.id != emp['address_home_id']:
                    emp_upd.update({'address_home_id': emp['address_home_id']})
                if not emp_brw.job_id or \
                        emp_brw.job_id.id != emp['job_id']:
                    emp_upd.update({'job_id': emp['job_id']})
                if emp_upd:
                    obj_emp.write(cr, uid, emp_id, emp_upd, context=context)
        return imported

    #~ AR-I

    def _get_ari(self, cr, uid, profit_db, field_list, context=None):
        context = context or {}

        params = {'limit': context.get('records_limit', ''),
                  'from': context.get('import_from'),
                  'to': context.get('import_to')}
        sql = '''
            select %(limit)s rtrim(e.cod_emp) as code,
                   rtrim(e.nombres) as name,
                   rtrim(e.ci) as identification_id,
                   v.val_n as salary,
                   isnull(ts.today_salary, 0) as today_salary,
                   isnull(tt.today_tax, 0) as today_tax
            from snemple e
            left join snem_va v on e.cod_emp = v.cod_emp and v.co_var = 'A001'
            left join (
                select cod_emp, sum(case when n.tipo=1 then monto
                                         when n.tipo=2 then -monto
                                         else 0 end) as today_salary
                from snnomi n
                left join snconcep c on n.co_conce = c.co_conce
                where c.campo2='ARC' and
                      n.fec_emis between '%(from)s' and '%(to)s'
                group by cod_emp) as ts on e.cod_emp = ts.cod_emp
            left join (
                select cod_emp, sum(monto) as today_tax from snnomi n
                where n.co_conce in ('R005','R855') and
                      n.fec_emis between '%(from)s' and '%(to)s'
                group by cod_emp) as tt on e.cod_emp = tt.cod_emp
            where e.status = 'A'
            order by code
            ''' % params
        data_list = self._exec_sql(
            cr, uid, profit_db, sql, context=context)
        return self._clean_data_list(data_list, field_list)

    def _import_ar_i(self, cr, uid, profit_db, context=None):
        '''
        Create list with employees salaries fro AR-I.
        model: tcv_rrhh_ari_forms
        Need a basic and empty ar-i (in draft) to load data
        '''
        context = context or {}
        imported = 0
        obj_emp = self.pool.get('hr.employee')
        frm_obj = self.pool.get('tcv.rrhh.ari.forms')
        ari_obj = self.pool.get('tcv.rrhh.ari')
        ari_ids = ari_obj.search(cr, uid, [('state', '=', 'draft')])
        if not ari_ids or len(ari_ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Can\t find AR-I in draft to load data'))
        ari_id = ari_ids[0]
        ari = ari_obj.browse(cr, uid, ari_id, context=context)
        if ari.forms_ids:
            forms_ids = frm_obj.search(
                cr, uid, [('ari_id', '=', ari_id)])
            if forms_ids:
                frm_obj.unlink(cr, uid, forms_ids, context=context)
        date = time.strptime(ari.date, '%Y-%m-%d')
        if date.tm_mon == 1:
            act_mon = date.tm_mon - 1  # Month for calculation
        else:
            act_mon = date.tm_mon
        field_list = ['code', 'name', 'identification_id', 'salary',
                      'today_salary', 'today_tax']
        data_list = self._get_ari(
            cr, uid, profit_db, field_list, context)

        for item in data_list:
            emp_id = obj_emp.search(cr, uid, [('code', '=', item['code'])])
            if emp_id:
                emp = obj_emp.browse(cr, uid, emp_id[0], context=context)
                if context.get('force_months'):
                    months = context.get('force_months')
                else:
                    months = 12 - act_mon
                #~ The estimated anual salary is calcutated using this:
                #~ amount =
                #~ 12 months * salary or (total_salary + (next months * salary)
                #~ 1 month vacations = salary (bv) (bono)
                #~ 4 month utilities = year_salary / 12 * 4
                mon_sal_12 = (item['salary'] * months) + item['today_salary']
                mon_sal_bv = item['salary']
                uti_sal = 4 * (mon_sal_12 / 12) if context.get('est_util') \
                    else 0
                amount = mon_sal_12 + mon_sal_bv + uti_sal
                data = {
                    'ari_id': ari_id,
                    'employee_id': emp.id,
                    'family_chrg': emp.family_chrg,
                    'income_ids': [(0, 0, {'name': emp.company_id.name,
                                           'amount': amount,
                                           })],
                    'today_salary': item['today_salary'],
                    'today_tax': item['today_tax'],
                    }
                frm_obj.create(cr, uid, data, context)
                imported += 1
        return imported

    ##--------------------------------------------------------- function fields

    _columns = {
        'profit_id': fields.many2one(
            'tcv.profit.import.config', 'Database name', required=True,
            readonly=True, states={'draft': [('readonly', False)]}),
        'data_type': fields.selection(
            [('contract', 'Contracts'),
             ('concept', 'Concepts'),
             ('job', 'Jobs (only assigned)'),
             ('employee', 'Employees (And partners if necessary)'),
             ('ar-i', 'AR-I Employees and salaries'),
             ],
            string='Data type', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many(
            'tcv.payroll.import.profit.lines', 'line_id', 'Profit data',
            readonly=True),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('load', 'Load')],
            string='State', required=True, readonly=True),
        'limit': fields.integer(
            'Limit records', readonly=True,
            states={'draft': [('readonly', False)]},
            help="limit the profit query to this number of record (0 = all)"),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'date_start': fields.date(
            'From', required=False, select=True),
        'date_end': fields.date(
            'To', required=False, select=True),
        'est_util': fields.boolean(
            'Estimate utls'),
        'force_months': fields.integer(
            'Force months qty', digits_compute=dp.get_precision('Account'),
            help="Set months to be projected (0=auto)"),
        }

    _defaults = {
        'state': lambda *a: 'draft',
        'est_util': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_data(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        lines = []
        for item in self.browse(cr, uid, ids, context=context):
            if item.limit:
                context.update({'records_limit': 'top(%s)' % item.limit})
            if item.data_type == 'contract':
                lines = self._get_contracts(cr, uid, item.profit_id,
                                            ['code', 'name'], context=context)
            elif item.data_type == 'concept':
                lines = self._get_concepts(cr, uid, item.profit_id,
                                           ['code', 'name'], context=context)
            elif item.data_type == 'job':
                lines = self._get_jobs(cr, uid, item.profit_id,
                                       ['code', 'name'], context=context)
            elif item.data_type == 'employee':
                lines = self._get_employees(cr, uid, item.profit_id,
                                            ['code', 'name'], context=context)
            elif item.data_type == 'ar-i':
                context.update({
                    'import_from': item.date_start,
                    'import_to': item.date_end,
                    'est_util': item.est_util,
                    'force_months': item.force_months,
                    })
                lines = self._get_ari(
                    cr, uid, item.profit_id, ['code', 'name'],
                    context=context)
            if lines:
                self.write(
                    cr, uid, [item.id],
                    {'name': _('%s records loaded!') % len(lines),
                     'line_ids': [(0, 0, x) for x in lines],
                     'state': 'load'},
                    context=context)
        return lines

    def button_clear_data(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_lines = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_lines.append((2, l.id))
            if unlink_lines:
                self.write(
                    cr, uid, [item.id],
                    {'name': _('%s records cleared!') % len(unlink_lines),
                     'line_ids': unlink_lines,
                     'state': 'draft'},
                    context=context)
        return unlink_lines

    def button_import_data(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        for item in self.browse(cr, uid, ids, context={}):
            if item.limit:
                context.update({'records_limit': 'top(%s)' % item.limit})
            imported = 0
            if item.data_type == 'contract':
                imported = self._import_contracts(cr, uid, item.profit_id,
                                                  context=context)
            elif item.data_type == 'concept':
                imported = self._import_concepts(cr, uid, item.profit_id,
                                                 context=context)
            elif item.data_type == 'job':
                imported = self._import_jobs(cr, uid, item.profit_id,
                                             context=context)
            elif item.data_type == 'employee':
                imported = self._import_employees(cr, uid, item.profit_id,
                                                  context=context)
            elif item.data_type == 'ar-i':
                context.update({
                    'import_from': item.date_start,
                    'import_to': item.date_end,
                    'est_util': item.est_util,
                    'force_months': item.force_months,
                    })
                imported = self._import_ar_i(cr, uid, item.profit_id,
                                             context=context)
            self.write(
                cr, uid, [item.id],
                {'name': _('%s records imported!') % imported,
                 'state': 'done'},
                context=context)
        return True

    def button_close(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_profit()


##--------------------------------------------- tcv_payroll_import_profit_lines


class tcv_payroll_import_profit_lines(osv.osv_memory):

    _name = 'tcv.payroll.import.profit.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.payroll.import.profit', 'Profit', required=True,
            ondelete='cascade'),
        'code': fields.char(
            'Code', size=16, required=True, readonly=False),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'type': fields.char(
            'Type', size=16, required=True, readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_profit_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

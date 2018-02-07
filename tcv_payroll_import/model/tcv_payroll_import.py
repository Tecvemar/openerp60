# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-18
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
#~ import time
#~ import netsvc

##---------------------------------------------------------- tcv_payroll_import


class tcv_payroll_import(osv.osv):

    _name = 'tcv.payroll.import'

    _description = ''

    _order = 'name desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _get_jobs_list(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_cfg = self.pool.get('tcv.profit.import.config')
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            if obj_cfg.get_profit_db_cursor(
                    cr, uid, [item.profit_id.id], context={}):
                obj_cfg.exec_sql(
                    '''
                    select distinct rtrim(co_cargo) as job from snnomi n
                    left join snemple e on n.cod_emp = e.cod_emp
                    where n.co_cont = '%s' and n.fec_emis = '%s'
                    ''', (item.contract_id.code, item.payroll_date))
                job_list = obj_cfg.fetchall()
                res = [x['job'] for x in job_list]
        return res

    def _check_invalid_jobs(self, cr, uid, jobs, context=None):
        if not jobs:
            return []
        job_ids = []
        obj_hrj = self.pool.get('hr.job')
        obj_pij = self.pool.get('tcv.payroll.import.job')
        for job_code in jobs:
            job_id = obj_hrj.search(cr, uid, [('code', '=', job_code)])
            if not job_id:
                job_id = obj_hrj.create(
                    cr, uid, {'code': job_code,
                              'name': _('-- Unknown job --')
                              }, context={})
                obj_pij.create(cr, uid, {'hr_job_id': job_id}, context)
            else:
                if not obj_pij.search(cr, uid, [('hr_job_id', '=', job_id)]):
                    obj_pij.create(cr, uid, {'hr_job_id': job_id[0]}, context)
        sql = """select id from hr_job where code in %(jobs)s"""
        #~ % str(jobs)[1:-1]. replace('L', '')
        params = {'jobs': tuple([x.strip() for x in jobs])}
        cr.execute(sql, params)
        jobs_ids = [x[0] for x in cr.fetchall()]
        sql = """
        select id from tcv_payroll_import_job
        where hr_job_id in %(jobs_ids)s and
        (concepts_table_id is null or
         analytic_account_id is null or
         payable_account_id is null)
        """
        #~ % str(jobs_ids)[1:-1]. replace('L', '')
        cr.execute(sql, {'jobs_ids': tuple(jobs_ids)})
        res = cr.fetchall()
        job_ids = [x[0] for x in res]
        if job_ids:
            sql = """
            update tcv_payroll_import_job
            set need_review = True
            where id in %(job_ids)s
            """
            #~ % str(job_ids)[1:-1]. replace('L', '')
            cr.execute(sql, {'job_ids': tuple(job_ids)})
        return job_ids

    def _get_used_concepts(self, cr, uid, ids, context=None):
        if not ids:
            return []
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_cfg = self.pool.get('tcv.profit.import.config')
        res = []
        for item in self.browse(cr, uid, ids, context=context):
            if obj_cfg.get_profit_db_cursor(
                    cr, uid, [item.profit_id.id], context=context):
                obj_cfg.exec_sql(
                    '''
                    select distinct rtrim(n.co_conce) as concept
                    from snnomi n
                    left join snemple e on n.cod_emp = e.cod_emp
                    left join snconcep c on n.co_conce = c.co_conce
                    where n.co_cont = '%s' and n.fec_emis = '%s' and
                          (c.noenviar = 0 or c.tipo != 4)
                    ''', (item.contract_id.code, item.payroll_date))
                concept_list = obj_cfg.fetchall()
                res = [x['concept'] for x in concept_list]
        return res

    def _get_payroll_receipt_list(self, cr, uid, item, context=None):
        context = context or {}
        receipt_list = []
        obj_cfg = self.pool.get('tcv.profit.import.config')
        if obj_cfg.get_profit_db_cursor(
                cr, uid, [item.profit_id.id], context=context):
            obj_cfg.exec_sql(
                '''
                select n.reci_num, rtrim(n.cod_emp) as cod_emp,
                       rtrim(e.co_cargo) as co_cargo,
                       sum(case when tipo = 1 then monto
                           when tipo in (2,3) then -monto
                           else 0 end) as monto
                from snnomi n
                left join snemple e on n.cod_emp = e.cod_emp
                where n.co_cont = '%s' and n.fec_emis = '%s'
                group by n.reci_num, n.cod_emp, e.co_cargo
                ''', (item.contract_id.code, item.payroll_date))
            receipt_list = obj_cfg.fetchall()
        return receipt_list

    def _get_data_id(self, cr, uid, model, field, value):
        obj_data = self.pool.get(model)
        ids = obj_data.search(cr, uid, [(field, '=', value)])
        return ids and ids[0] or 0

    def _get_payroll_receipts(self, cr, uid, ids, context=None):
        if not ids:
            return []
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_pij = self.pool.get('tcv.payroll.import.job')
        for item in self.browse(cr, uid, ids, context=context):
            receipt_list = self._get_payroll_receipt_list(
                cr, uid, item, context=context)
            payroll_amount = 0
            receipt_qty = 0
            receipts = []
            for r in receipt_list:
                employee_id = self._get_data_id(
                    cr, uid, 'hr.employee', 'code', r['cod_emp'])
                if not employee_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\' find employee with code: %s') % r['cod_emp'])
                job_id = self._get_data_id(
                    cr, uid, 'hr.job', 'code', r['co_cargo'])
                import_job_id = self._get_data_id(
                    cr, uid, 'tcv.payroll.import.job', 'hr_job_id', job_id)
                if not import_job_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\' find job code: %s') % r['co_cargo'])
                pij_brw = obj_pij.browse(
                    cr, uid, import_job_id, context=context)
                data = {
                    'name': r['reci_num'],
                    'employee_id': employee_id,
                    'job_id': job_id,
                    'import_job_id': import_job_id,
                    'concepts_table_id': pij_brw.concepts_table_id.id,
                    'amount': r['monto'],
                    }
                if r['monto'] < 0:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t process recipit:\n' +
                          '\tNro: %s, Empl: [%s], Amount: %s') %
                        (r['reci_num'], r['cod_emp'], r['monto']))
                payroll_amount += r['monto']
                receipt_qty += 1
                receipts.append((0, 0, data))
        return {'payroll_amount': payroll_amount,
                'receipt_qty': receipt_qty,
                'receipt_ids': receipts,
                }

    def _check_jobs_table(self, cr, uid, ids, jobs, context=None):
        if not ids or not jobs:
            return []
        context = context or {}
        obj_hrj = self.pool.get('hr.job')
        obj_pij = self.pool.get('tcv.payroll.import.job')
        obj_itl = self.pool.get('tcv.payroll.import.table.lines')
        obj_pid = self.pool.get('tcv.payroll.import.data')
        concepts = self._get_used_concepts(cr, uid, ids, context=context)
        concept_dict = {}
        #~ Get used concepts ids: concept_dict = {'code': concept_id}
        for code in concepts:
            pid_id = obj_pid.search(
                cr, uid, [('code', '=', code), ('type', '=', 'concept')])
            if pid_id:
                pid_id = pid_id[0]
            else:
                #~ Create concept's code if not exists
                pid_id = obj_pid.create(
                    cr, uid, {'code': code,
                              'name': _('-- Unknown concept --'),
                              'type': 'concept',
                              'need_review': True
                              }, context)
            concept_dict.update({code: pid_id})
        need_review_ids = []
        #~ Check if all used concepts are assigned
        hrj_ids = obj_hrj.search(cr, uid, [('code', 'in', jobs)])
        job_ids = obj_pij.search(cr, uid, [('hr_job_id', 'in', hrj_ids)])
        for job in obj_pij.browse(cr, uid, job_ids, context={}):
            if job.concepts_table_id:
                for code in concepts:
                    concept_id = concept_dict.get(code)
                    itl_ids = obj_itl.search(
                        cr, uid, [('concept_id', '=', concept_id),
                                  ('table_id', '=', job.concepts_table_id.id)])
                    if itl_ids:
                        itl = obj_itl.browse(
                            cr, uid, itl_ids[0], context=context)
                        if itl.move_type != 'emp_receivable' and \
                                not itl.account_id:
                            need_review_ids.append(itl.id)
                        if itl.move_type == 'for_others' and \
                                not itl.payable_acc_id:
                            need_review_ids.append(itl.id)

                    else:
                        itl_id = obj_itl.create(
                            cr, uid, {'concept_id': concept_id,
                                      'table_id': job.concepts_table_id.id},
                            context)
                        need_review_ids.append(itl_id)
        if need_review_ids:
            sql = """
            update tcv_payroll_import_table_lines
            set need_review = True
            where id in %(need_review_ids)s
            """
            #~ % str(need_review_ids)[1:-1]. replace('L', '')
            cr.execute(sql, {'need_review_ids': tuple(need_review_ids)})
        return need_review_ids

    def _get_payroll_lines(self, cr, uid, receipt, context=None):
        context = context or {}
        obj_cfg = self.pool.get('tcv.profit.import.config')
        res = []
        if obj_cfg.get_profit_db_cursor(
                cr, uid, [receipt.receipt_id.profit_id.id], context=context):
            obj_cfg.exec_sql(
                '''
                select rtrim(e.cod_emp) as cod_emp,
                       rtrim(e.co_cargo) as co_cargo,
                       rtrim(n.co_conce) as co_conce,
                       n.monto, n.tipo
                from snnomi n
                left join snemple e on n.cod_emp = e.cod_emp
                left join snconcep c on n.co_conce = c.co_conce
                where n.reci_num = '%s' and (c.noenviar = 0 or c.tipo != 4)
                order by n.co_conce
                ''', (receipt.name))
            res = obj_cfg.fetchall()
        return res

    def _create_account_move_lines(self, cr, uid, receipt, context=None):
        payroll = self._get_payroll_lines(cr, uid, receipt, context=context)
        move_lines = []
        concepts = {}
        for concept in receipt.concepts_table_id.line_ids:
            con_code = concept.concept_id.code
            concepts.update(
                {con_code: {'code': con_code,
                            'name': concept.concept_id.name,
                            'account_id': concept.account_id and
                            concept.account_id.id or 0,
                            'payable_acc_id': concept.payable_acc_id.id,
                            'move_type': concept.move_type,
                            }})
        emp_brw = receipt.employee_id
        for pay_line in payroll:
            co_conce = pay_line['co_conce']
            monto = float(pay_line['monto'])
            debits = [1]
            tipo = 'db' if pay_line['tipo'] in debits else 'cr'
            if not concepts.get(co_conce):
                raise osv.except_osv(
                    _('Error!'),
                    _('Missing concept: %s, Update concept\'s table and ' +
                      'reprocess payrol data') %
                    co_conce)
            data = {
                'company_id': receipt.receipt_id.company_id.id,
                'partner_id': (emp_brw.partner_id and
                               emp_brw.partner_id.id) or 0,
                'account_id': concepts[co_conce]['account_id'],
                'name': concepts[co_conce]['name'],
                'debit': monto if tipo == 'db' else 0,
                'credit': monto if tipo == 'cr' else 0,
                }
            move_lines.append((0, 0, data))
            if concepts[co_conce]['move_type'] == 'for_others':
                tipo = 'cr' if tipo == 'db' else 'db'
                for_others = {}
                for_others.update(data)
                data.update({
                    'account_id': concepts[co_conce]['payable_acc_id']})
                for_others.update({
                    'debit': monto if tipo == 'db' else 0,
                    'credit': monto if tipo == 'cr' else 0,
                    })
                move_lines.append((0, 0, for_others))
            elif concepts[co_conce]['move_type'] == 'emp_receivable':
                account_id = emp_brw.receivable_account_id and \
                    emp_brw.receivable_account_id.id or 0
                if not account_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must indicate an account for %s') %
                        receipt.employee_id.name)
                data.update({'account_id': account_id})
        #  Select account from contract (data) or from job's table
        if receipt.receipt_id.contract_id.payable_account_id:
            account_id = receipt.receipt_id.contract_id.payable_account_id.id
        else:
            account_id = receipt.import_job_id.payable_account_id.id
        data = {
            'company_id': receipt.receipt_id.company_id.id,
            'partner_id': emp_brw.partner_id and emp_brw.partner_id.id or 0,
            'account_id': account_id,
            'name': _('Payroll: [%s] %s') %
            (receipt.receipt_id.contract_id.code, receipt.employee_id.name),
            'debit': 0,
            'credit': receipt.amount,
            }
        move_lines.append((0, 0, data))
        return move_lines

    def _create_grouped_move_lines(self, cr, uid, item, data, context=None):
        '''
        Return dict with grouped account move
        '''
        lines = {}
        for acc_move in data:
            for acc_line in acc_move['line_id']:
                li = acc_line[2]
                if li['account_id'] in lines:
                    lines[li['account_id']]['debit'] += li['debit']
                    lines[li['account_id']]['credit'] += li['credit']
                else:
                    lines[li['account_id']] = {
                        'account_id': li['account_id'],
                        'name': _('Payroll: %s Date: %s') % (
                            item.contract_id.code, item.payroll_date),
                        'debit': li['debit'],
                        'credit': li['credit'],
                        'company_id': item.company_id.id,
                        }
        line_ids = []
        for move in lines.values():
            if move['debit'] and move['credit']:
                move2 = move.copy()
                move['credit'] = 0
                move2['debit'] = 0
                line_ids.append((0, 0, move2))
            line_ids.append((0, 0, move))
        return {
            'ref': _('Payroll: %s Date: %s') %
            (item.contract_id.code,
             item.payroll_date),
            'journal_id': item.journal_id.id,
            'period_id': item.period_id.id,
            'date': item.date,
            'company_id': item.company_id.id,
            'state': 'draft',
            'to_check': False,
            'line_id': line_ids,
            }

    def _create_account_move(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_move = self.pool.get('account.move')
        obj_pir = self.pool.get('tcv.payroll.import.receipt')
        group_move = []
        move_id = None
        for item in self.browse(cr, uid, ids, context={}):
            for receipt in item.receipt_ids:
                move = {
                    'ref': _('Payroll: %s Date: %s Rcb: %s') %
                    (item.contract_id.code,
                     item.payroll_date,
                     receipt.name),
                    'journal_id': item.journal_id.id,
                    'period_id': item.period_id.id,
                    'date': item.date,
                    'company_id': item.company_id.id,
                    'state': 'draft',
                    'to_check': False,
                    'narration': '%s\n%s' % (receipt.employee_id.name,
                                             receipt.job_id.name,)
                    }
                lines = self._create_account_move_lines(
                    cr, uid, receipt, context=context)
                lines.reverse()
                total = 0
                for x, y, l in lines:
                    total += l['debit'] - l['credit']
                if abs(total) > 0.001:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Unbalanced account move: (%s) %s\n' +
                          'Check concept accounting settings.\n' +
                          'Amount: %.2f') %
                        (receipt.name, receipt.employee_id.name, total))
                move.update({'line_id': lines})
                if not item.contract_id.group_payroll_lines:
                    move_id = obj_move.create(cr, uid, move, context)
                    if move_id:
                        obj_move.post(cr, uid, [move_id], context=context)
                        obj_pir.write(
                            cr, uid, receipt.id, {'move_id': move_id},
                            context=context)
                else:
                    group_move.append(move)
            #  Generate only grouped account move
            if group_move:
                move = self._create_grouped_move_lines(
                    cr, uid, item, group_move, context)
                move_id = obj_move.create(cr, uid, move, context)
                if move_id:
                    obj_move.post(cr, uid, [move_id], context=context)
                    self.write(
                        cr, uid, item.id, {'grouped_move_id': move_id},
                        context=context)
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=16, required=False, readonly=True),
        'contract_id': fields.many2one(
            'tcv.payroll.import.data', 'Contract', required=True,
            ondelete='restrict', domain=[('type', '=', 'contract')],
            readonly=True, states={'draft': [('readonly', False)]}),
        'payroll_date': fields.date(
            'Payroll date', required=True, select=True,
            readonly=True, states={'draft': [('readonly', False)]},
            help="Payroll processing date"),
        'date': fields.date(
            'Accounting date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True,
            help="Accounting date for payroll"),
        'period_id': fields.many2one(
            'account.period', 'Period', required=True, ondelete="restrict",
            readonly=True, states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True,
            domain="[('type','=','general')]", ondelete='restrict',
            readonly=True, states={'draft': [('readonly', False)]}),
        'receipt_ids': fields.one2many(
            'tcv.payroll.import.receipt', 'receipt_id', 'Payroll receipts',
            readonly=True),
        'profit_id': fields.many2one(
            'tcv.profit.import.config', 'Database name', required=True,
            readonly=True, states={'draft': [('readonly', False)]}),
        'receipt_qty': fields.integer(
            'Receipt qty', readonly=True, help="Quantity of payroll receipts"),
        'payroll_amount': fields.float(
            'Payroll amount', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Total amount of payroll"),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'),
             ('confirm', 'Confirmed'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'grouped_move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The grouped account move of this payroll.",
            select=True, readonly=True),
        }

    _defaults = {
        'name': lambda *a: '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'user_id': lambda s, c, u, ctx: u,
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ('payroll_uniq', 'UNIQUE(contract_id,payroll_date)',
         'The payroll is already registered!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_cancel_all_move_ids(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        cancel_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for receipt in item.receipt_ids:
                if receipt.move_id.state == 'posted':
                    cancel_ids.append(receipt.move_id.id)
        if cancel_ids:
            obj_mov = self.pool.get('account.move')
            obj_mov.button_cancel(cr, uid, cancel_ids, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date):
        res = {}
        if date:
            obj_per = self.pool.get('account.period')
            per_id = obj_per.find(cr, uid, date)
            res.update({'period_id': per_id and per_id[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.payroll.import')})
        res = super(tcv_payroll_import, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_receipts = []
        for item in self.browse(cr, uid, ids, context={}):
            for m in item.receipt_ids:
                unlink_receipts.append((2, m.id))
        vals = {'state': 'draft',
                'receipt_qty': 0,
                'payroll_amount': 0,
                'receipt_ids': unlink_receipts}
        return self.write(cr, uid, ids, vals, context)

    def button_confirm(self, cr, uid, ids, context=None):
        context = context or {}
        vals = {'state': 'confirm'}
        vals.update(self._get_payroll_receipts(cr, uid, ids))
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        if self._create_account_move(cr, uid, ids, context):
            vals = {'state': 'done'}
            return self.write(cr, uid, ids, vals, context)
        return False

    def button_cancel(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        obj_pir = self.pool.get('tcv.payroll.import.receipt')
        move_unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            if item.grouped_move_id:
                self.write(
                    cr, uid, [item.id], {'grouped_move_id': 0}, context)
                move_unlink_ids.append(item.grouped_move_id)
            for receipt in item.receipt_ids:
                if receipt.move_id:
                    obj_pir.write(
                        cr, uid, [receipt.id], {'move_id': 0}, context)
                    move_unlink_ids.append(receipt.move_id.id)
        print move_unlink_ids
        obj_move.unlink(cr, uid, move_unlink_ids, context)
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_confirm(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            data = self._get_payroll_receipt_list(cr, uid, item)
            if not data:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t find valid payroll receipts.'))
        jobs = self._get_jobs_list(cr, uid, ids)
        invalid_job_ids = self._check_invalid_jobs(cr, uid, jobs)
        concept_ids = self._check_jobs_table(cr, uid, ids, jobs, context={})
        if jobs and invalid_job_ids or concept_ids:
            #~ Need commit because this error condition causes a "raise"
            #~ in test_confirm and this causes a transaction's rollback
            cr.commit()
            raise osv.except_osv(
                _('Error!'),
                _('Please review missing settings in job\'s ' +
                  'tables and/or Concept\'s tables'))

        return True

    def test_done(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.grouped_move_id.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t cancel a process while account ' +
                          'move state <> "Draft"'))
            for receipt in item.receipt_ids:
                if receipt.move_id:
                    if receipt.move_id.state == 'posted':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t cancel a process while account ' +
                              'move state <> "Draft"'))
                    for line in receipt.move_id.line_id:
                        if line.reconcile_id:
                            raise osv.except_osv(
                                _('Error!'),
                                _('Can\'t cancel a process while account ' +
                                  'move line is reconciled'))
        return True


tcv_payroll_import()


##-------------------------------------------------- tcv_payroll_import_receipt


class tcv_payroll_import_receipt(osv.osv):

    _name = 'tcv.payroll.import.receipt'

    _description = ''

    _order = 'name'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'receipt_id': fields.many2one(
            'tcv.payroll.import', 'Payroll', required=True,
            ondelete='cascade'),
        'name': fields.integer(
            'Receipt', required=True, readonly=True),
        'employee_id': fields.many2one(
            'hr.employee', 'Employee', required=True,
            ondelete='restrict', readonly=True),
        'job_id': fields.many2one(
            'hr.job', 'Job', required=True,
            ondelete='restrict', readonly=True),
        'import_job_id': fields.many2one(
            'tcv.payroll.import.job', 'Payroll job', required=True,
            ondelete='restrict', readonly=True),
        'concepts_table_id': fields.many2one(
            'tcv.payroll.import.table', 'Concept\'s table', required=False,
            ondelete='restrict'),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='set null',
            help="The move of this payroll receipt.", select=True,
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_payroll_import_receipt()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

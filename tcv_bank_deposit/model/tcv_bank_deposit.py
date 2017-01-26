# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Updated: Juan Márquez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import time


class tcv_bank_deposit(osv.osv):

    _name = 'tcv.bank.deposit'

    _description = 'Modulo de gestion de planillas de depositos bancarios'

    _order = 'date,ref desc'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
        ]

    def copy(self, cr, uid, id, default={}, context=None, done_list=[],
             local=False):
        item = self.browse(cr, uid, id, context=context)
        default = default or {}
        default = default.copy()
        default.update({'name': (item.name or '') + '(copy)',
                        'ref': '/',
                        'narration': '',
                        'state': 'draft',
                        'move_id': False,
                        })
        return super(tcv_bank_deposit, self).copy(cr, uid, id, default,
                                                  context=context)

    def _compute_comission(self, cr, uid, line, comission):
        total = (line.amount * comission) / 100
        res = round(total, self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account'))
        return res

    def _total_deposit_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for dep in self.browse(cr, uid, ids, context=context):
            res[dep.id] = {
                'cash_total': 0.0,
                'cheq_total': 0.0,
                'debit_total': 0.0,
                'comission_total': 0.0,
                'prepaid_total': 0.0,
                'amount_total': 0.0,
            }
            for line in dep.line_ids:
                if line.origin.type == 'cash':
                    res[dep.id]['cash_total'] += line.amount
                elif line.origin.type == 'cheq':
                    res[dep.id]['cheq_total'] += line.amount
                elif line.origin.type == 'debit':
                    res[dep.id]['debit_total'] += line.amount
                    res[dep.id]['comission_total'] += self._compute_comission(
                        cr, uid, line, line.rel_comission)
                    res[dep.id]['prepaid_total'] += self._compute_comission(
                        cr, uid, line, line.rel_prepaid_tax)
            if res[dep.id]['comission_total']:
                res[dep.id]['comission_total'] += dep.comission_dif
            res[dep.id]['amount_total'] = res[dep.id]['cash_total'] + \
                res[dep.id]['cheq_total'] + res[dep.id]['debit_total'] - \
                res[dep.id]['comission_total'] - res[dep.id]['prepaid_total']
        return res

    def _get_account_balance(self, cr, uid, account_id, operator,
                             date_balance, context):
        cr.execute('''
            select sum(debit-credit) as balance_in_currency
            FROM account_move_line l
            left join account_move m on l.move_id = m.id
            WHERE l.account_id = %s AND
                  l.date %s '%s' AND
                  m.state = 'posted'
            ''' % (account_id, operator, date_balance))
        return cr.dictfetchone()['balance_in_currency'] or 0

    _columns = {
        'ref': fields.char(
            'Reference', size=32, readonly=True),
        'name': fields.char(
            'Document number', size=32, readonly=True,
            states={'draft': [('readonly', False)]}),
        'bank_journal_id': fields.many2one(
            'account.journal', 'Bank journal', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True, readonly=True,
            ondelete='restrict', states={'draft': [('readonly', False)]}),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The move of this entry line.", select=2, readonly=True),
        'state': fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        'check_total': fields.float(
            'Total', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]}),
        'comission_dif': fields.float(
            'Comission dif. (±1)', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]},
            help="You can set here a small diference in calculated " +
            "comission ammount."),
        'line_ids': fields.one2many(
            'tcv.bank.deposit.line', 'line_id', 'Details', readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='cascade'),
        'cash_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Cash total (+)', store=False, multi='all'),
        'cheq_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Cheq total (+)', store=False, multi='all'),
        'debit_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Debit/credit total (+)', store=False, multi='all'),
        'comission_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Comission total (-)', store=False, multi='all'),
        'prepaid_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Prepaid tax total (-)', store=False, multi='all'),
        'amount_total': fields.function(
            _total_deposit_all, method=True,
            digits_compute=dp.get_precision('Account'),
            string='General total (=)', store=False, multi='all'),
        'narration': fields.text(
            'Notes', readonly=False),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'name': lambda *a: '',
        'check_total': lambda *a: 0.0,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').
        browse(cr, uid, uid, c).company_id.currency_id.id,
        'state': 'draft',
        }

    _sql_constraints = [
        ('deposit_name_uniq', 'UNIQUE(name, bank_journal_id)',
         'The reference must be unique for this bank journal!'),
        ('max_comission_dif', 'CHECK(comission_dif between -1 and 1)',
         'The maximum difference comsion must be in -1 to 1 range'),
        ]

    def compute_dif(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.check_total != item.amount_total:
                dif = item.amount_total - item.check_total + item.comission_dif
                if abs(dif) > 1:
                    raise osv.except_osv(
                        _('Error!'),
                        _(u'Computed dif > ±1'))
                self.write(
                    cr, uid, [item.id],
                    {'comission_dif': dif},
                    context=context)
        return True

    def button_draft(self, cr, uid, ids, context=None):
        obj = self.pool.get('tcv.bank.deposit')
        vals = {'state': 'draft'}
        return obj.write(cr, uid, ids, vals, context)

    def button_posted(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiplies validations not allowed.'))
        for item in self.browse(cr, uid, ids, context={}):
            if not item.ref or item.ref == '/':
                ref = self.pool.get('ir.sequence').get(cr, uid, 'bank.deposit')
            else:
                ref = item.ref
        context.update({'deposit_reference': ref})
        obj = self.pool.get('tcv.bank.deposit')
        vals = {'state': 'posted',
                'ref': ref,
                'move_id': self._gen_account_move(cr, uid, ids, context)}
        return obj.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        for dep in self.browse(cr, uid, ids, context={}):
            if dep.state == 'posted':
                if dep.move_id.id:
                    obj_move = self.pool.get('account.move')
                    move = obj_move.browse(
                        cr, uid, dep.move_id.id, context=None)
                    if move.state == 'draft':
                        recon_id = 0
                        for line in dep.line_ids:
                            if line.move_line and not recon_id and \
                                    line.move_line.reconcile_id.id:
                                recon_id = line.move_line.reconcile_id.id
                        if recon_id:
                            obj_lines = self.pool.get('account.move.line')
                            rec_ids = obj_lines.search(
                                cr, uid, [('reconcile_id', '=', recon_id)])
                            obj_lines._remove_move_reconcile(
                                cr, uid, rec_ids, context=None)
                        obj = self.pool.get('tcv.bank.deposit')
                        vals = {'state': 'cancel', 'move_id': 0}
                        res = obj.write(cr, uid, ids, vals, context)
                        obj_move.unlink(cr, uid, [move.id])
            elif dep.state == 'draft':
                obj = self.pool.get('tcv.bank.deposit')
                vals = {'state': 'cancel', 'move_id': 0}
                res = obj.write(cr, uid, ids, vals, context)
        return res

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_posted(self, cr, uid, ids, *args):
        so_brw = self.browse(cr, uid, ids, context={})
        for dep in so_brw:
            if time.strptime(dep.date, '%Y-%m-%d') > time.localtime():
                raise osv.except_osv(_('Invalid date!'),
                                     _('The date must be <= today.'))
            if not dep.amount_total:
                raise osv.except_osv(_('No valid amount!'),
                                     _('The total must be > 0'))
            if abs(dep.amount_total - dep.check_total) > 0.0001:
                raise osv.except_osv(
                    _('Bad total !'),
                    _('Please verify the lines of the document ! The real ' +
                      'total does not match the computed total.'))
            if not dep.name:
                raise osv.except_osv(
                    _('Error!'), _('You must set a document number.'))
            #~ lines checks
            chk_origin = {'cash_cheq': 0}
            chk_cash = {}
            chk_cash_info = []
            for line in dep.line_ids:
                config = self.pool.get('tcv.bank.config.detail').browse(
                    cr, uid, line.origin.id, context=None)
            #~ Validar grupo de medios de pagos seleccionados
                if config.type in ('cash', 'cheq'):
                    chk_origin['cash_cheq'] += 1
                    if config.type == 'cash':
                        #~ Acumulate cash total in chk_cash
                        if line.origin.id not in chk_cash:
                            chk_cash.update({line.origin.id: 0})
                            chk_cash_info.append({
                                'cash_acc':
                                line.rel_journal.default_debit_account_id.id,
                                'code': line.origin.id,
                                'acc_name':
                                line.rel_journal.default_debit_account_id.name
                                })
                        chk_cash[line.origin.id] += line.amount
                else:  # debit and credit
                    if line.origin.id not in chk_origin:
                        chk_origin.update({line.origin.id: 1})
                    else:
                        chk_origin[line.origin.id] += 1

                if not line.rel_journal.default_debit_account_id.id or \
                        not line.rel_journal.default_credit_account_id.id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must set a debit and credit account for ' +
                          'journal: %s.') % (line.rel_journal.name))
                if config.type == 'debit' and \
                        dep.bank_journal_id.id != config.bank_journal_id.id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The bank journal differs from bank journals ' +
                          'payment method. You must be select: %s journal') %
                        (config.bank_journal_id.name))
            if not chk_origin['cash_cheq']:
                chk_origin.pop('cash_cheq')
            if len(chk_origin) != 1:
                raise osv.except_osv(
                    _('Error!'),
                    _('You can not mix different types of payments.'))
            #~ Check if cash account balance < cash in deposit
            for cash in chk_cash_info:
                balance = self._get_account_balance(
                    cr, uid, cash['cash_acc'], '<=', dep.date, context={})
                if chk_cash[cash['code']] > balance:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not deposit more cash than is in the ' +
                          'account: %s: %.2f') % (cash['acc_name'], balance))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        so_brw = self.browse(cr, uid, ids, context={})
        for dep in so_brw:
            if dep.move_id.id:
                move = self.pool.get('account.move').browse(
                    cr, uid, dep.move_id.id, context=None)
                if move.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not cancel a deposit while the account ' +
                          'move is posted.'))
        return True

    def button_calculate_click(self, cr, uid, ids, context=None):
        return True

    def _gen_account_move_line(self, company_id, partner_id, account_id,
                               name, debit, credit):
        return (0, 0, {
            'auto': True,
            'company_id': company_id,
            'partner_id': partner_id,
            'account_id': account_id,
            'name': name,
            'debit': round(debit, 2),
            'credit': round(credit, 2),
            'reconcile': False,
            })

    def _gen_account_move(self, cr, uid, ids, context=None):
        need_reconcile = False
        so_brw = self.browse(cr, uid, ids, context={})
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        move_id = None
        for dep in so_brw:
            obj_cfg = self.pool.get('tcv.bank.config')
            cfg_id = obj_cfg.search(
                cr, uid, [('company_id', '=', dep.company_id.id)])[0]
            config = obj_cfg.browse(cr, uid, cfg_id, None)
            move = {
                'ref': '%s - Nro %s' % (context.get('deposit_reference', 'dp'),
                                        dep.name),
                'journal_id': dep.bank_journal_id.id,
                'date': dep.date,
                'period_id': obj_per.find(cr, uid, dep.date)[0],
                'company_id': dep.company_id.id,
                'state': 'draft',
                'to_check': False,
                'narration': '',
                }
            lines = []
            for line in dep.line_ids:  # move line for deposit lines
                lines.append(self._gen_account_move_line(
                    dep.company_id.id,
                    line.partner_id.id,
                    line.rel_journal.default_credit_account_id.id,
                    line.move_line.name or line.rel_journal.name,
                    0,
                    line.amount))
                need_reconcile = need_reconcile or line.move_line.id
            if dep.comission_total:  # move line for comission
                lines.append(self._gen_account_move_line(
                    dep.company_id.id,
                    False,
                    config.acc_bank_comis.id,
                    move['ref'],
                    dep.comission_total,
                    0))
            if dep.prepaid_total:  # move line for prepaid tax
                lines.append(self._gen_account_move_line(
                    dep.company_id.id,
                    False,
                    config.acc_prepaid_tax.id,
                    move['ref'],
                    dep.prepaid_total,
                    0))
            # move line for deposit's bank credit
            lines.append(self._gen_account_move_line(
                dep.company_id.id,
                False,
                dep.bank_journal_id.default_debit_account_id.id,
                move['ref'],
                dep.check_total,
                0))
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            obj_move.post(cr, uid, [move_id], context=context)
            if need_reconcile and move_id:
                self.do_reconcile(cr, uid, dep, move_id, context)
        return move_id

    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        unlink_ids = []
        for dep in so_brw:
            if dep.state in ('draft', 'cancel'):
                unlink_ids.append(dep['id'])
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete deposit(s) that are already postedd!'))
        super(tcv_bank_deposit, self).unlink(cr, uid, unlink_ids, context)
        return True

    def do_reconcile(self, cr, uid, dep, move_id, context):
        obj_mov = self.pool.get('account.move')
        move = obj_mov.browse(cr, uid, move_id, context=context)
        rec_ids = []
        for line in dep.line_ids:
            if line.move_line.id:
                rec_ids.append(line.move_line.id)
            for move_line in move.line_id:
                if line.amount == move_line.credit and \
                        line.move_line.account_id.id == \
                        move_line.account_id.id:
                    if move_line.id not in rec_ids:
                        rec_ids.append(move_line.id)
        if rec_ids:
            obj_move_line = self.pool.get('account.move.line')
            obj_move_line.reconcile(cr, uid, rec_ids, context=context)
        return True

tcv_bank_deposit()


class tcv_bank_deposit_line(osv.osv):

    _name = 'tcv.bank.deposit.line'

    _description = ''

    _rec_name = 'move_line'

    _columns = {
        'line_id': fields.many2one(
            'tcv.bank.deposit', 'Deposit lines', required=True,
            ondelete='cascade'),
        'origin': fields.many2one(
            'tcv.bank.config.detail', 'Origin', required=True,
            ondelete='restrict'),
        'rel_journal': fields.related(
            'origin', 'journal_id', type='many2one',
            relation='account.journal', string='Journal name',
            store=False, readonly=True),
        'rel_forced': fields.related(
            'origin', 'force_detail', type='boolean', string='Forced',
            store=False, readonly=True),
        'rel_comission': fields.related(
            'origin', 'bank_comission', type='float', string='Comission',
            store=False, readonly=True),
        'rel_prepaid_tax': fields.related(
            'origin', 'prepaid_tax', type='float', string='Comission',
            store=False, readonly=True),
        'move_line': fields.many2one(
            'account.move.line', 'Move', ondelete='restrict',
            domain="[('journal_id', '=', rel_journal), " +
            "('debit','>', 0), ('reconcile_id', '=', 0)]"),
        'partner_id': fields.related(
            'move_line', 'partner_id', type='many2one',
            relation='res.partner', string='Partner', store=False,
            readonly=True),
        'amount_move': fields.related(
            'move_line', 'debit', type='float', string='Move amount',
            store=False),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        'dep_date': fields.related(
            'line_id', 'date', string='Deposit date', readonly=True,
            type='date'),
        }

    _defaults = {
        }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        so_brw = self.browse(cr, uid, ids, context={})
        res = []
        for record in so_brw:
            name = '%s: %s - %s' % (record.origin.name, record.move_line.ref,
                                    record.partner_id.name)
            res.append((record.id, name))
        return res

    def on_change_move_line(self, cr, uid, ids, move_line):
        res = {'value': {'amount_view': 0.0}}
        if move_line:
            move = self.pool.get('account.move.line').browse(
                cr, uid, move_line, context=None)
            res = {'value': {'amount_move': move.debit,
                             'amount': move.debit,
                             'partner_id': move.partner_id.id}}
        return res

    def on_change_origin(self, cr, uid, ids, origin):
        res = {}
        if origin:
            org = self.pool.get('tcv.bank.config.detail').browse(
                cr, uid, origin, context=None)
            res = {'value': {'rel_journal': org.journal_id.id,
                             'rel_forced': org.force_detail,
                             'rel_comission': org.bank_comission,
                             'rel_prepaid_tax': org.prepaid_tax}}
        return res

    def create(self, cr, uid, vals, context=None):
        if 'amount' not in vals and 'amount_move' in vals:
            vals.update({'amount': vals['amount_move']})
        return super(tcv_bank_deposit_line, self).create(
            cr, uid, vals, context)


tcv_bank_deposit_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

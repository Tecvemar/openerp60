# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#        Gestiona el proceso de sincronización de cuentas
#        Manages the account's synchronization process
#
##############################################################################
#~ from datetime import datetime
from osv import fields,osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time



class account_account(osv.osv):

    _inherit = "account.account"

    _columns = {
        'sync_type': fields.selection([('full_sync', 'Full sync'),('no_child_sync', "No child's' sync"), ('no_sync', 'No sync')], string='Account sync', required=True, readonly=False,help='Set the method for account sync between'),
        }

    _defaults = {
        'sync_type':'no_sync',
        }

    _sql_constraints = [
        ('no_view_no_sync_chield', "CHECK (not((type!='view') and (sync_type='no_child_sync')))", 'If the account type <> view the sync_type must be full or none'),
    ]


    def _get_sync_data(self,cr,uid,context):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if context == None:
            context = {}
        company_id = context.get('company_id', user.company_id.id)
        sync_obj = self.pool.get('tcv.account.sync')
        sync_ids = sync_obj.search(cr, uid, [('company_id', '=', company_id)])
        if not sync_ids:
            raise osv.except_osv(_('Error!'), _('Invalid account sync settings.'))
        sync_conf = sync_obj.browse(cr,uid,sync_ids[0],context=context)
        ## Get compnies list
        obj = self.pool.get('res.company')
        company_ids = obj.search(cr, sync_conf.user_id.id, [('id', '!=', False)])
        if sync_conf.company_id.id in company_ids:
            company_ids.remove(sync_conf.company_id.id)
        try:
            user_name = sync_conf.user_id.name
        except:
            user_name = 'User id: %s'%sync_conf.user_id.id
            pass
        res = {
            'company_id':company_id,
            'company_ids':company_ids,
            'sync_user':sync_conf.user_id.id,
            'user_name':user_name,
            'main_company':sync_conf.company_id.id,
            'main_name':sync_conf.partner_id.name,
            }
        return res


    def _prepare_account_sync(self,cr, uid, ids, vals, action, sync_args, context):
        acc_obj = self.pool.get('account.account')
        sync_data = self._get_sync_data(cr,uid,context)
        if sync_data['company_id'] != sync_data['main_company'] and sync_data['sync_user'] != uid:
            raise osv.except_osv(_('Error!'), _('This account is synchronized. Any updates to this account must be done from company: %s or by user :%s.')%(sync_data['main_name'],sync_data['user_name']))
        sync_vals = []
        for c in  sync_data['company_ids']:
            tmp_data = {}
            tmp_data.update(vals)
            if action == 'create':
                acc_id = acc_obj.search(cr, sync_data['sync_user'], [('code', '=', sync_args['parent_code']),('company_id','=',c)])
                if not acc_id or len(acc_id) > 1:
                    raise osv.except_osv(_('Error!'), _('Sync error (parent_id): Action: %s, Company: %s, Account: %s, acc_id: %s.')%(action,c,sync_args['code'],acc_id))
                tmp_data.update({'parent_id':acc_id[0]})
            else:
                acc_id = acc_obj.search(cr, sync_data['sync_user'], [('code', '=', sync_args['code']),('company_id','=',c)])
                if len(acc_id) > 1:
                    raise osv.except_osv(_('Error!'), _('Sync error (account_id): Action: %s, Company: %s, Account: %s, acc_id: %s')%(action,c,sync_args['code'],acc_id))
                tmp_data.update({'account_id':acc_id if acc_id else None})
            tmp_data.update({'sync_action':action,'company_id':c,'sync_user':sync_data['sync_user']})
            sync_vals.append(tmp_data)
        return sync_vals


    def create(self, cr, uid, vals, context=None):
        if not vals.get('sync_type'):
            vals.update({'sync_type':'no_sync'})
        context = context or {}
        acc_obj = self.pool.get('account.account')
        sync_data = self._get_sync_data(cr,uid,context)
        ## Validate code in others companies
        if vals.get('sync_type') != 'no_sync' and not context.get('no_sync_data'):
            acc_ids = acc_obj.search(cr, sync_data['sync_user'], [('code', '=', vals.get('code'))])
            if acc_ids:
                comp = ''
                for i in acc_ids:
                    a = acc_obj.browse(cr,sync_data['sync_user'],i,context=context)
                    comp = '%s,\n\t%s'%(comp,a.company_id.name) if comp else '\t%s'%a.company_id.name
                raise osv.except_osv(_('Error!'), _("Can't create account te code exits in:\n%s")%comp)
        ## Bug #1028921 - no_chield_sync no funciona
        parent = vals.get('parent_id') and self.pool.get('account.account').browse(cr,uid,vals['parent_id'],context=context)
        if parent and parent.sync_type == 'full_sync' and not context.get('no_sync_data'):
            if sync_data['company_id'] != sync_data['main_company'] and sync_data['sync_user'] != uid:
                raise osv.except_osv(_('Error!'), _("Can't create account, the account parent's (%s-%s) is full sinchronized")%(parent.code,parent.name))
            if vals['sync_type'] == 'no_sync':
                raise osv.except_osv(_('Error!'), _("The account parent's (%s-%s) is full sinchronized, the sync type must be 'full' or 'no chield sync'")%(parent.code,parent.name))
        ## If account.type == view -> sync_typee in 'no_sync','fuul_sync'
        if vals.get('sync_type') == 'no_child_sync' and vals.get('type') != 'view':
            vals.update({'sync_type':'full_sync'})
        res = super(account_account, self).create(cr, uid, vals, context)
        if not context.get('no_sync_data'):
            so_brw = self.browse(cr,uid,[res],context)
            for brw in so_brw:
                if brw.sync_type != 'no_sync': ## full_sync or no_child_sync
                    sync_args = {'code':brw.code,'parent_code':brw.parent_id.code,'sync_type':brw.sync_type}
                    sync_vals = self._prepare_account_sync(cr, uid, res, vals, 'create', sync_args, context)
                    for v in sync_vals:
                        super(account_account, self).create(cr, v['sync_user'], v, context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        ## Bug #1028907 - tcv_account_sync full_sync -> no_sync
        obj_acc = self.pool.get('account.account')
        old_sync_type = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        old_data = obj_acc.browse(cr,uid,ids,context=context)
        for i in old_data:
            old_sync_type.update(
                {i.company_id.id: {
                    vals.get('code', i.code): {    #  Use new code or old code for dict key
                        'sync_type': i.sync_type,  #  Save sync_type
                        'old_code': i.code,        #  Save old code
                        }}})
            if vals.get('sync_type') == 'no_sync':
                if not vals.get('parent_id'):
                    parent = i.parent_id
                else:
                    parent = obj_acc.browse(cr,uid,vals['parent_id'],context=context)
                if parent.sync_type == 'full_sync':
                    raise osv.except_osv(_('Error!'), _("The account parent's (%s-%s) is full sinchronized, the sync type must be 'full' or 'no chield sync'")%(parent.code,parent.name))
        if vals.get('sync_type'):
            chield_ids = obj_acc.search(cr, uid, [('parent_id', 'in', ids)])
            for id in chield_ids:
                chield = obj_acc.browse(cr,uid,id,context=context)
                if vals['sync_type'] == 'no_sync' and chield.sync_type in ['full_sync','no_child_sync']:
                    raise osv.except_osv(_('Error!'), _("The chield account (%s-%s) is sinchronized, can't set account to 'no sync'")%(chield.code,chield.name))
                elif vals['sync_type'] == 'full_sync' and chield.sync_type == 'no_sync':
                    raise osv.except_osv(_('Error!'), _("The chield account (%s-%s) is not sinchronized, can't set account to '%s'")%(chield.code,chield.name,vals['sync_type']))
        res = super(account_account, self).write(cr, uid, ids, vals, context)
        for brw in self.browse(cr, uid, ids, context):
            ## If sync (brw.sync_type != 'no_sync') or was sync (ost['sync_type'] != 'no_sync')
            ost = old_sync_type[brw.company_id.id][brw.code]  #  Old account data
            if brw.sync_type != 'no_sync' or ost['sync_type'] != 'no_sync': #  full_sync or no_child_sync
                sync_args = {'code': ost.get('old_code', brw.code), 'parent_code': brw.parent_id.code, 'sync_type': brw.sync_type}
                sync_vals = self._prepare_account_sync(cr, uid, ids, vals, 'write', sync_args, context)
                for v in sync_vals:
                    if v['account_id']:
                        super(account_account, self).write(cr, v['sync_user'], v['account_id'], v, context)
                    else:
                        # If account is created no_sync and then change to sync need to create account in other companies
                        data = obj_acc.read(cr,uid,brw.id,[])
                        for f in ['id','parent_left','parent_right','create_uid','create_date','write_date','write_uid']:
                            if data.has_key(f):
                                data.pop(f)
                        data.update(v)
                        data['user_type'] = isinstance(data['user_type'], (int, long)) and [data['user_type']] or data['user_type']
                        data.update({'user_type': data['user_type'][0]})
                        context.update({'no_sync_data':True}) # This key disable de sync process temporally (only for this case)
                        obj_acc.create(cr,v['sync_user'],data,context)
        return res


    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr,uid,ids,context)
        for brw in so_brw:
            if brw.sync_type != 'no_sync': ## full_sync or no_child_sync
                sync_args = {'code':brw.code,'parent_code':brw.parent_id.code,'sync_type':brw.sync_type}
                sync_vals = self._prepare_account_sync(cr, uid, ids, {}, 'unlink', sync_args, context)
                for v in sync_vals:
                    if v['account_id']:
                        super(account_account, self).unlink(cr, v['sync_user'], v['account_id'], context)
        res = super(account_account, self).unlink(cr, uid, ids, context)
        return res


account_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

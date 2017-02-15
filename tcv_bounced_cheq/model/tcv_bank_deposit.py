# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# -*- encoding: utf-8 -*-
##############################################################################
#    
#~ 
#~ 
#
##############################################################################
from osv import fields,osv
from tools.translate import _

class tcv_bank_deposit(osv.osv):
    
    _inherit = "tcv.bank.deposit"
    
    def test_cancel(self, cr, uid, ids, *args):
        so_brw = self.browse(cr,uid,ids,context={})
        obj_bou = self.pool.get('tcv.bounced.cheq')
        for dep in so_brw:
            bou_list = ''
            for line in dep.line_ids:
                if line.origin.use_bounced_cheq:
                    bounced_ids = obj_bou.search(cr, uid, [('deposit_line_id', '=', line.id)])
                    if bounced_ids:
                        bou = obj_bou.browse(cr,uid,bounced_ids,context=None)   
                        for b in bou:
                            bou_list += ' - %s %14s %14.2f\n'%(b.ref,b.name,b.amount)
            if bou_list:                
                raise osv.except_osv(_('Error!'),_('You can not cancel a deposit because (at least) one of the lines is a bounced cheq:\n%s')%(bou_list[:-1]))
        super(tcv_bank_deposit, self).test_cancel(cr, uid, ids, args)    
        return True
    
tcv_bank_deposit()   


class tcv_bank_deposit_line(osv.osv):

    
    _inherit = "tcv.bank.deposit.line" 

    
    def _is_bounced_cheq(self, cr, uid, ids, name, args, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            obj = self.pool.get('tcv.bounced.cheq')
            src = obj.search(cr, uid, [('deposit_line_id', '=', line.id)])
            result[line.id] = (src != [])

        return result


    def _search_bounced_cheq(self, cr, uid, obj, name, args, context=None):
        """ 
        @return: Ids of bounced_cheqs
        """       
        if not len(args):
            return []

        res = []     
        if args[0][0] == name and name == 'was_bounced':
            if (args[0][1] == '=' and args[0][2] == False) or (args[0][1] == '!=' and args[0][2] == True):
                clause = 'not'
            else:
                clause = '' 
            sql = '''
            select dl.id, dc.use_bounced_cheq from tcv_bank_deposit_line dl 
            left join tcv_bank_config_detail dc on dl.origin = dc.id
            where dl.id %s in (select deposit_line_id from tcv_bounced_cheq) 
                  and dc.use_bounced_cheq = True            
            '''%clause
            cr.execute(sql)
            data = cr.fetchall()
            if not data:
                res = [('id', '=', 0)]
            res = [('id', 'in', [x[0] for x in data])]
        return res
        
        
    def _get_bounced_id(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.was_bounced:
                obj = self.pool.get('tcv.bounced.cheq')
                obj_id = obj.search(cr, uid, [('deposit_line_id', '=', line.id)])
                if obj_id:
                    data = obj.browse(cr,uid,obj_id[0],context=context)
                    result[line.id] = (data.id,data.ref)
        return result

    
    _columns = {
        'can_bounced':fields.related('origin','use_bounced_cheq', type='boolean', string='Can be bounced', readonly=True), 
        'cheq_number':fields.related('move_line','ref', type='char', string='Cheq number', readonly=True), 
        'was_bounced':fields.function(_is_bounced_cheq, method=True, type='boolean', string='Was bounced', fnct_search=_search_bounced_cheq),
        'bounced_id': fields.function(_get_bounced_id, method=True, type='many2one', relation='tcv.bounced.cheq', string='Bounced ref'),
        }


tcv_bank_deposit_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

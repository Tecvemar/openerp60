# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-10-01
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##----------------------------------------------------------------------- users


class users(osv.osv):

    _inherit = 'res.users'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def user_belongs_groups(self, cr, uid, groups_required, context={}):
        '''
        # groups is a tuple with group.name values
        groups = ('Accounting / Manager','Other / group name')
        '''
        group_ids = self.pool.get('res.groups').\
            search(cr, uid, [('name', 'in', groups_required)])
        user_groups = self.browse(cr, uid, uid, context=context).groups_id
        for group in user_groups:
            if group.id in group_ids:
                return True  # Yes, the user belongs group
        return False

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

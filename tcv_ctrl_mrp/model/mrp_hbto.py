# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
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


from datetime import datetime
from osv import fields,osv
import pooler
import decimal_precision as dp
import time


# ---------------------------------------------------  Base class

class hbto_base(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_tcv_base
    '''

    _name = 'hbto.base'
    _description = __doc__

    def _compute_run_time(self, cr, uid, ids, date_start, date_end, context=None):
        ''' must return date_end - date_start in hours'''
        rc_brw = self.browse(cr, uid, ids,context=context)
        #~ print rc_brw
        #~ start = rc_brw.date_start
        #~ end =rc_brw.date_end
        #~ time = self.read(cr, uid, ids, ['date_start'],context=context)
        #~ print date_start, date_end
        #~ if date_start and date_end:
            #~ return date_end-date_start
        return {}


    _columns = {
        'name':fields.char('Reference', size=64, required=False, readonly=False),  
        'mrp_production_id': fields.many2one('mrp.production', 'Manufacturing Order'),
        'date_start':fields.datetime('Start date', Select=True),
        'date_end':fields.datetime('Finish date', Select=True),
        'run_time':fields.function(_compute_run_time, method=True, type='time', string='Production run time'),
        'author_id': fields.many2one('res.users', 'Author'),
        'note':fields.text('Description'),
        #'prior_mrp_production_id':fields.many2one('mrp.ctrl.tcv.base', 'Prior'),
        #'next_mrp_production_id':fields.many2one('mrp.ctrl.tcv.base', 'Next'),
        'company_id':fields.many2one('res.company','Company',required=True),
        # crear campo reference
        }

    def on_change_run_time(self, cr, uid, ids, date_start, date_end):
        res = {'value':{'run_time':self._compute_run_time(cr,uid,ids,date_start, date_end)}}
        return res
    
hbto_base()


# ---------------------------------------------------  Telares

class hbto_telar(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_telar
    '''
    
    _name = 'hbto.telar'
    _description = __doc__
    _inherits = {'hbto.base':'base_id'}
    _rec_name = "base_id"
    _columns = {
        'base_id':fields.many2one('hbto.base', 'Base'),
        'lines_ids':fields.one2many('hbto.line','telar_id','Details'),
        }
hbto_telar()


# ---------------------------------------------------  Telares.line

class hbto_line(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_telar_line
    '''
    
    _name = 'hbto.line'
    _description = __doc__
    _rec_name = 'telar_id'
    _columns = {
        'telar_id':fields.many2one('hbto.telar', 'Telar'),
        }
        
    def _rotate(self):
        ''' read lot info and swap heigth & width '''
        return 0

hbto_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

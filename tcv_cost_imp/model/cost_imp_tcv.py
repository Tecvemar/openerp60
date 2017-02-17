import time
from datetime import datetime
from osv import osv, fields
import pooler
from tools.translate import _
import decimal_precision as dp

class cost_imp_tcv(osv.osv):
	"""OpenERP Model : cost_imp_tcv"""
	_name = 'cost.imp.tcv'
	_description = __doc__

	_columns = {
		'name':fields.char('Reference', size=16, required=True, select=True),
		'exp_number':fields.char('Record', size=16),
		'open_date':fields.date('Open Date', required=True, select=True),
		'close_date':fields.date('Close Date'),
		'partner_id':fields.many2one('res.partner', 'Customs Broker', required=False, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, change_default=True),
	    'folder':fields.char('Folder', size=10),
        'company_id': fields.many2one('res.company','Company',required=True,select=1),		
		'create_uid':  fields.many2one('res.users', 'Responsible'),
        'invoice_ids': fields.many2many('account.invoice', 'purchase_invoice_rel', 'purchase_id', 'invoice_id', 'Invoices', help="Invoices generated for a purchase order"),

			      }
	
	_defaults = {
		'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'cost.imp.tcv'),
		'open_date': lambda *a: time.strftime('%Y-%m-%d'),
	    'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'cost.imp.tcv', context=c),

		}
	_sql_constraints = [
        ('name_uniq', 'unique(name)', 'Reference must be unique!'),
        ('run_time_gt_zero', 'check(open_date<=close_date)', 'The closing date must be greater than the opening date!'),
    ]
    #~ TODO Validar que una Factura aparezca una sola vez en un expediente.
    #~ TODO Colocar un campo Main Purchase que seleccione en el campo Purchase de todas las facturas, la que sea principal.
cost_imp_tcv()

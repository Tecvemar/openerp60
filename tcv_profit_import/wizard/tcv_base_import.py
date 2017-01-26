# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 23/04/2013
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################

from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler

##---------------------------------------------------------------------------------------- tcv_base_import

class tcv_base_import(osv.osv_memory):

    _name = 'tcv.base.import'

    _description = ''

    _import_settings = {'get_document_sql':'',
                        'get_lines_sql':'',
                        }

    ##------------------------------------------------------------------------------------
    
    def decode_tax_id(self,cr,uid,tax_code,type):
        '''
        tax_code 1, 6 or 9 (integer)
        type 'Compras' or 'Ventas'
        '''
        obj_tax = self.pool.get('account.tax')
        taxes = range(12)
        taxes[1] = 'IVA 12% '+type
        taxes[6] = 'IVA 0% '+type
        taxes[9] = 'IVA 8% '+type
        return obj_tax.search(cr, uid, [('name', '=', taxes[int(tax_code)])])[0]
        

    def encode_date(self,adate):
        return ('%s'%adate).split()[0] # solo considerar la fecha sin la hora       


    def profit_2_openerp_currency(self,profit_id,curency):
        #~ Se define un diccionario por empresa profit
        dict_curency = {0:{ 'BSF':'VEB',
                            'US$':'USD',
                            'EUR':'EUR',
                        }}
        if not dict_curency[profit_id].has_key(curency):
            print 'Moneda: "%s"'%curency
        else:
            return dict_curency[profit_id][curency]        
        return 'VEB'
        
        
    def profit_2_openerp_salesman(self,profit_id,co_ven):
        #~ Se define un diccionario por empresa profit
        dict_co_ven = {0:{  '000001':'admin0',
                            '069153':'avisicchio0',
                            '095813':'amillan',
                            '099307':'oramos',
                            '139086':'mruscino',
                            '297382':'rpadovani',
                            '332038':'jmarquez0',
                            '560616':'rbvisicchio',
                            '580025':'gruscino',
                            '903810':'gvisicchio',
                            '9999':'admin0',
                            'E039':'jhuggins'}
                        }    
        if not dict_co_ven[profit_id].has_key(co_ven):
            print 'Vendedor: "%s"'%co_ven
        else:
            return dict_co_ven[profit_id][co_ven]        
            
            
    def _get_config(self,cr,uid,ids,context=None):
        so_brw = self.browse(cr,uid,ids,context={})   
        obj_ = self.pool.get('')
        
        
    def decode_aux02(self,a2):
        """
        this code splits the data in aux02 (from profit db)
        """
        if a2:
            data = a2.split(';')
            pc=le=he=wi=0
            ub=''
            if len(data) == 4:
                if data[0]:
                    pc = int(float(data[0]))
                    wi = float(data[0])
                if data[1]:
                    le = float(data[1].replace(',','.'))
                if data[2]:
                    he = float(data[2])
                if data[3]:
                    ub = data[3]
            if he > le:
                he,le = le,he        
            res = {'pieces':pc,
                   'length':le,
                   'heigth':he,
                   'width':wi,
                   'location':ub,}
        else:           
            res = {'pieces':0,
                   'length':0,
                   'heigth':0,
                   'width':0,
                   'location':0,}
        return res              
    

    ##------------------------------------------------------------------------------------ _internal methods

    def _get_profit_document(self,cr,uid,ids,context=None):
        if context is None:
             context = {}
        data = self.browse(cr,uid,ids,context=context)[0]
        obj_cfg = self.pool.get('tcv.profit.import.config')
        if not context.get('profit_config'):
            profit_config = obj_cfg.browse(cr,uid,data.profit_id.id,context=context)
            context.update({'profit_config':profit_config})
        if obj_cfg.get_profit_db_cursor(cr,uid,[data.profit_id.id],context):
            profit_table = obj_cfg.exec_sql(self._import_settings['get_document_sql'],(data.name))
            return obj_cfg.fetchone()
        return {}


    def _get_profit_document_lines(self,cr,uid,ids,context=None):
        if context is None:
             context = {}
        data = self.browse(cr,uid,ids,context=context)[0]
        obj_cfg = self.pool.get('tcv.profit.import.config')
        if not context.get('profit_config'):
            profit_config = obj_cfg.browse(cr,uid,data.profit_id.id,context=context)
            context.update({'profit_config':profit_config})
        if obj_cfg.get_profit_db_cursor(cr,uid,[data.profit_id.id],context):
            profit_table = obj_cfg.exec_sql(self._import_settings['get_lines_sql'],(data.name))
            return obj_cfg.fetchall()
        return {}


    def _update_document_data(self,cr,uid,ids,document,context=None):
        '''
        This update field values in destination model
        need to be overwrited in inherited models
        '''
        return {}


    def _update_lines_data(self,cr,uid,ids,lines,context=None):
        '''
        This update field values in destination model
        need to be overwrited in inherited models
        '''
        return {}


    def _get_profit_code(self,cr, uid, model_name, type, profit_code,context=None):
        obj_pcd = self.pool.get('tcv.profit.codes')
        code_ids = obj_pcd.search(cr, uid, [('name ', '=', model_name),('type ', '=', type),('profit_code','=',profit_code)])
        if code_ids:
            code = obj_pcd.browse(cr,uid,code_ids,context=context)
            if code and len(code) == 1:
                return code[0].code_id
        print '_get_profit_code', model_name,profit_code
        return 0
        
    ##------------------------------------------------------------------------------------ function fields

    _columns = {
        'name': fields.char('Document number', 32, readonly=False, required=True),
        'profit_id': fields.many2one('tcv.profit.import.config', 'Database name', readonly=False, required=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ public methods

    ##------------------------------------------------------------------------------------ buttons (object)

    def import_button_click(self, cr, uid, ids, context=None):
        if context is None:
             context = {}
        so_brw = self.browse(cr,uid,ids,context=context)[0]
        context.update({'profit_config':so_brw.profit_id,'tcv_base_import_brw':so_brw})
        
        document = self._get_profit_document(cr,uid,ids,context=context)
        context.update({'profit_document':document})
        if self._update_document_data(cr,uid,ids,document,context=context):
            lines = self._get_profit_document_lines(cr,uid,ids,context=context)
            self._update_lines_data(cr,uid,ids,lines,context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------------------------------ on_change...

    ##------------------------------------------------------------------------------------ create write unlink

    ##------------------------------------------------------------------------------------ Workflow

tcv_base_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

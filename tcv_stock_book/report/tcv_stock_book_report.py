# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
import time
import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_stock_book_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_stock_book_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_rif': self._get_rif,
            #~ 'get_slab_list': self._get_slab_list,
            })
        self.context = context

    def _get_rif(self, vat=''):
        if not vat:
            return []
        return vat[2:].replace(' ', '')
#~
#~
    #~ def _get_slab_list(self,obj):
        #~ res = map(lambda x: {'name':x,'size':'','thickness':''},range(1,63))
        #~ for r in res:
            #~ if int(r['name']) <= int(obj.slab_qty):
                #~ r.update({'size':'%.3f x %.3f'%(obj.net_length,obj.net_heigth),'thickness':'%s'%obj.thickness})
        #~ return res


report_sxw.report_sxw(
    'report.tcv_stock_book.tcv_stock_book_report',
    'tcv.stock.book',
    'addons/tcv_stock_book/report/tcv_stock_book_report.rml',
    parser=parser_tcv_stock_book_report,
    header=False
)

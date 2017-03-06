# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_load_external_data
#
#
##############################################################################
#~ from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc
import logging
logger = logging.getLogger('server')


##------------------------------------------------------ tcv_load_external_data


class tcv_load_external_data(osv.osv_memory):

    _name = 'tcv.load.external.data'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _exec_sql(self, cr, uid, profit_id, sql, context):
        obj_cfg = self.pool.get('tcv.profit.import.config')
        try:
            obj_cfg.get_profit_db_cursor(
                cr, uid, [profit_id], context=context)
            obj_cfg.exec_sql(sql)
            if 'select' in sql.lower():
                return obj_cfg.fetchall()
            elif 'update' in sql.lower() or 'insert' in sql.lower():
                obj_cfg.commit()
                return True
        except:
            logger.error(
                'Unable to execute external query (profit_id: %s):\n%s' %
                (profit_id, sql))
            raise osv.except_osv(
                _('Error!'),
                _('Profit: SQL Server communication error'))

    ##--------------------------------------------------------- function fields

    _columns = {
        'orig_db_id': fields.many2one(
            'tcv.profit.import.config', 'Origin DB name', required=True,
            readonly=False),
        'dest_db_id': fields.many2one(
            'tcv.profit.import.config', 'Destination DB name', required=True,
            readonly=False),
        'date_start': fields.date(
            'From', required=True, select=True),
        'date_end': fields.date(
            'To', required=True, select=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def dest_db_load_data(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.orig_db_id.company_ref:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must select an extarnal database related with ' +
                      'partner (%s %s)') % (item.orig_db_id.name,
                                            item.orig_db_id.company_ref))
            params = {'date_start': item.date_start,
                      'date_end': item.date_end,
                      }
            sql = """
                select ANO as 'year', MES as 'month',
                       sum(amount_sales) as amount_sales,
                       sum(tile_m2) as tile_m2,
                       sum(slab_m2) as slab_m2,
                       sum(return_m2) as return_m2
                from (
                select ANO, MES,
                   sum(monto) as amount_sales, 0 as tile_m2,
                   0 as slab_m2, 0 as return_m2
                from (
                   select year(fv.fec_emis) ANO, Month(fv.fec_emis) MES,
                          fv.monto_net-fv.monto_imp as monto, fv.monto_net,
                          fv.monto_imp
                   from docum_cc fv WHERE fv.anulado=0 and
                        fv.tipo_doc='FACT' and
                        fv.fec_emis BETWEEN '%(date_start)s' AND '%(date_end)s'
                   union all
                   select year(dv.fec_emis) ANO, Month(dv.fec_emis) MES,
                          -dv.tot_neto+dv.iva as monto,
                          -dv.tot_neto as monto_net,
                          -dv.iva as monto_imp
                   from dev_cli dv WHERE dv.anulada=0 and dv.nc_num > 0 and
                        dv.fec_emis BETWEEN '%(date_start)s' AND '%(date_end)s'
                ) as q group by ano, mes
                union all
                Select ANO, MES, 0 as amount_sales,
                       sum(BALDOSAS) as tile_m2, Sum(LAMINAS) as slab_m2,
                       Sum(DEVOLUCIONES) as return_m2
                from (Select Month(f.fec_emis) MES, year(f.fec_emis) ANO,
                             Case a.co_lin When 'BA' Then (r.total_art)
                                ELSE 0 END as BALDOSAS,
                             Case a.co_lin When 'LA' Then (r.total_art)
                                ELSE 0 END as LAMINAS,
                             r.total_dev DEVOLUCIONES
                      from reng_Fac r Left join art a on r.co_art = a.co_art
                      Left join Lin_art l on a.co_lin = l.co_lin
                      Left Join factura f on r.fact_num = f.fact_num
                      Where a.uni_venta = 'MT2' and f.anulada = 0 and
                           (a.co_lin = 'BA' or a.co_lin = 'LA') and
                            f.fec_emis BETWEEN '%(date_start)s' AND
                            '%(date_end)s') as subquery
                Group By mes, ano) as w
                Group By mes, ano
                Order By ano, mes
                """ % params
            logger.info(
                'Loading Related partners Profit sales data %s (id: %s)' %
                (item.orig_db_id.name, item.orig_db_id.company_ref))
            origen_data = self._exec_sql(
                cr, uid, item.orig_db_id.id, sql, context=context)
            for row in origen_data:
                params = {
                    'partner_id': item.orig_db_id.company_ref,
                    'year': row.get('year', 0),
                    'month': row.get('month', 0),
                    }
                sql = """
                select id, year, month from tcv_related_annual_sales
                where partner_id = %(partner_id)s and year = %(year)s and
                month = %(month)s
                """ % params
                values = self._exec_sql(
                    cr, uid, item.dest_db_id.id, sql, context=context)
                params = {
                    'partner_id': item.orig_db_id.company_ref,
                    'year': row.get('year', 0),
                    'month': row.get('month', 0),
                    'return_m2': float(row.get('return_m2', 0)),
                    'slab_m2': float(row.get('slab_m2', 0)),
                    'amount_sales': float(row.get('amount_sales', 0)),
                    'tile_m2': float(row.get('tile_m2', 0)),
                    }
                if values and values[0].get('id'):
                    params.update({'id': values[0].get('id')})
                    sql = """
                    UPDATE [tcv_related_annual_sales]
                    SET [amount_sales] = %(amount_sales)s,
                        [slab_m2] = %(slab_m2)s,
                        [tile_m2] = %(tile_m2)s,
                        [return_m2] = %(return_m2)s
                    WHERE [id] = %(id)s and [partner_id] = %(partner_id)s
                    """ % params
                    logger.info(
                        'Update related partners sales ' +
                        '%s (id: %s, period: %04d/%02d)' %
                        (item.orig_db_id.name, item.orig_db_id.company_ref,
                         params.get('year', 0), params.get('month', 0)))
                else:  # [tecvemar_com_ve_sql].[dbo].
                    sql = """
                        INSERT INTO [tcv_related_annual_sales]
                           ([partner_id], [year], [month], [amount_sales],
                            [slab_m2], [tile_m2], [return_m2])
                        VALUES (
                           %(partner_id)s, %(year)s, %(month)s,
                           %(amount_sales)s, %(slab_m2)s, %(tile_m2)s,
                           %(return_m2)s)""" % params
                    logger.info(
                        'Insert related partners sales ' +
                        '%s (id: %s, period: %04d/%02d)' %
                        (item.orig_db_id.name, item.orig_db_id.company_ref,
                         params.get('year', 0), params.get('month', 0)))
                if sql:
                    self._exec_sql(
                        cr, uid, item.dest_db_id.id, sql, context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_load_external_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc
import pymssql


##---------------------------------------------------- tcv_profit_import_config


class tcv_profit_import_config(osv.osv):

    _name = 'tcv.profit.import.config'

    _description = ''

    _profit_conn = None
    _profit_cursor = None

    ##-------------------------------------------------------------------------

    def str_import(self, s):
        """
        This function "clean" the strings imported from profit
        """
        if s:
            s = s.replace(chr(10), ' ')
            s = s.replace(chr(13), ' ')
            s = s.replace('  ', ' ')
            s = s.replace('\n', '')
            s = s.replace('\t', '')
            s = s.strip()
        if s:
            s = unicode(s, 'latin-1').encode('utf-8')
            s = s.replace('', '€')
        return s

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'host': fields.char(
            'Host', size=32, required=True, readonly=False,
            help="Server ip or name"),
        'database': fields.char(
            'Database', size=32, required=True, readonly=False),
        'user': fields.char(
            'User', size=32, required=True, readonly=False),
        'password': fields.char(
            'Password', size=32, required=True, readonly=False),
        'company_ref': fields.integer(
            'Company ref #'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_profit_db_cursor(self, cr, uid, ids, context=None):
        '''
        ids: is a list with len() = 1 required, stores a id for one mssql
        connection settings (profit database)
        returns a cursor to mssql database
        '''
        if not ids or len(ids) != 1:
            return {}
        profit_db = self.browse(cr, uid, ids[0], context=context)
        self._profit_conn = pymssql.connect(
            host=profit_db.host, user=profit_db.user,
            password=profit_db.password, database=profit_db.database,
            as_dict=True)
        self._profit_cursor = self._profit_conn.cursor()
        return True

    def exec_sql(self, sql, params=()):
        '''
        execute a sql query
        '''
        if params:
            return self._profit_cursor.execute(sql % params)
        else:
            return self._profit_cursor.execute(sql)

    def fetchone(self):
        data = self._profit_cursor.fetchone()
        if data:
            for key in data:
                if type(data[key]) == str:
                    data.update({key: self.str_import(data[key])})
        return data

    def fetchall(self):
        data_list = self._profit_cursor.fetchall()
        for data in data_list:
            for key in data:
                if type(data[key]) == str:
                    data.update({key: self.str_import(data[key])})
        return data_list

    def commit(self):
        self._profit_conn.commit()
        return True

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_profit_import_config()

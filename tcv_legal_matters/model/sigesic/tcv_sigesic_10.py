# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-18
#    Version: 0.0.0.1
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

##------------------------------------------------------------ tcv_sigesic_0901


class tcv_sigesic_1001(osv.osv):

    _name = 'tcv.sigesic.1001'

    _description = 'Machinery\n' + \
                   'Datos de las Maquinarias para el Proceso Productivo'

    _csv_file_name = 'maquinarias_%s.csv'

    _csv_header = ('',)

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=100, required=False, readonly=False,
            help="Nombre: denominación de la máquina. Este nombre debe ser " +
            "único dentro del registro de maquinarias"),
        'country_id': fields.many2one(
            'res.country', 'Country',
            help="País Origen: nación donde se elaboró la máquina utilizada " +
            "por la unidad económica para la transformación de insumos en " +
            "bienes de consumo intermedio o final"),
        'description': fields.char(
            'Description', size=200,
            help="Descripción: Señale las características y usos " +
            "principales de la maquinaria"),
        'yead_adq': fields.integer(
            'Adquisition',
            help="Año Adquisición: año en que se compró la máquina " +
            "utilizada por la unidad económica para la transformación de " +
            "insumos en bienes de consumo intermedio o final"),
        'status': fields.selection(
            [('working', 'En funcionamiento'),
             ('stoped', 'Desincorporada'),
             ('maintenance', 'Parada por falta de repuesto o piezas')],
            string='Status', help="Estado de la Maquinaria: condición en la " +
            "que se encuentra actualmente la máquina y/o equipo utilizado " +
            "por la Unidad Económica, las mismas pueden ser: En " +
            "Funcionamiento: Seleccione si la máquina está operativa. " +
            "Desincorporada: Seleccione si la máquina no está operativa. " +
            "Parada por falta de repuestos ó piezas: Seleccione si la " +
            "máquina esta parada por falta de alguna(s) pieza(s) ó " +
            "repuesto(s) para su funcionamiento."),
        'plant': fields.selection(
            [('tecevmar', 'TECVEMAR'), ],
            string='Plant',
            help="Planta a la que está asociada la maquinaria."),
        'prod_line': fields.selection(
            [('granito', 'GRANITO'), ],
            string='Prod.line',
            help="Línea de producción/Estación de trabajo: seleccione a " +
            "que línea de producción o sección de trabajo corresponde la " +
            "máquina"),
        'yead_fab': fields.integer(
            'Fabrication', help="Año Fabricación: es el año de " +
            "fabricación de la máquina utilizada por la unidad económica " +
            "para la transformación de insumos en bienes de consumo " +
            "intermedio o final."),
        'service_life': fields.integer(
            'Service life', help="Vida Útil: Es el tiempo estimado que " +
            "debe durar la máquina cumpliendo de manera óptima con las " +
            "funciones para la cual fue diseñada (años)"),
        'amperage': fields.float(
            'Amperage', digits=(10, 2), readonly=False,
            help="Amperaje: indique la corriente en amperios (AMP)"),
        'voltage': fields.float(
            'Voltage', digits=(10, 2), readonly=False,
            help="Voltaje: indique la tensión (en voltios) que utiliza la " +
            "máquina"),
        'power': fields.float(
            'Power', digits=(10, 2), readonly=False,
            help="Potencia: indique en caballos de fuerza (HP)"),
        'water': fields.float(
            'Water', digits=(10, 2), readonly=False,
            help="Litros de Agua: indique la cantidad de agua que " +
            "utiliza la máquina mensualmente. Coloque cero (0) en caso de " +
            "no utilizar agua."),
        'fuel': fields.char(
            'Fuel type', size=100, help="Tipo combustible: Indique el " +
            "tipo de combustible que utiliza la máquina. Deje el campo " +
            "en blanco en caso de no usar ningún tipo de combustible"),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        'status': lambda *a: 'working',
        'plant': lambda *a: 'tecevmar',
        'prod_line': lambda *a: 'granito',
        'service_life': lambda *a: 1,
        }

    _sql_constraints = [
        ('service_life_range', 'CHECK(service_life between 1 and 100)',
         'The service life must be in 1-100 range!'),
        ('yead_adq_range', 'CHECK(yead_adq between 1918 and 2020)',
         'The year must be in 1918-2020 range!'),
        ('yead_fab_range', 'CHECK(yead_fab between 1918 and 2020)',
         'The year must be in 1918-2020 range!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def copy(self, cr, uid, id, default=None, context=None):
        brw = self.browse(cr, uid, id, context={})
        default = default or {}
        default.update({
            'data_year': brw.data_year + 1,
            })
        res = super(tcv_sigesic_1001, self).copy(cr, uid, id, default, context)
        return res

    def get_data_line(self, cr, uid, line_id, context):
        #~ def str_line(line):
            #~ return line and line.replace(';', ',') or ''
        #~ line = self.browse(cr, uid, line_id, context=context)
        return ('',
                )

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_1001()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

��    �      ,  �   <
      �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �                         
                                        "     %     (     +     /     E     I     R  3   `     �     �     �     �     �     �     �     �     �                    *  5   .  3   d  5   �     �     �     �  	   �     �                       '   8  &   `     �     �     �  "   �  $   �           (     7     ;     ?     D     J     O     b     s     �     �     �  X   �     �  2   �  :   &     a  0   �     �     �     �      �     �     �     �     �       9        H     ^     d     l  ;   t  	   �     �     �     �     �  &   
     1     @     C     F     I     L  *   S  !   ~  *   �  (   �  (   �  $        B     N     R     ^     t     x     �     �     �     �     �     �          $     -  %   F  N   l  L   �  &       /     5     8     >     E     J     O     [     b     r     �     �     �     �     �          (     >     W  -  p     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �     �                    
                    *     .     :  E   M     �     �     �     �     �     �     �     �                         /  5   3  9   i  9   �     �     �     �                              '      7   '   S   &   {      �      �      �   "   �   $   !     ;!     C!     R!     V!     Z!     `!     f!     m!     �!     �!     �!     �!     �!  X   �!     "  2   "  :   I"     �"  0   �"     �"     �"     �"  -   �"     #     #     &#     .#     7#  9   >#     x#     �#     �#     �#  ;   �#  	   �#     �#     $  "   $     8$  *   I$     t$     �$     �$     �$     �$     �$  0   �$  %   �$  /   �$  0   %  1   P%  +   �%     �%     �%     �%  !   �%     �%     �%     &  $   )&     N&     `&     }&  '   �&  	   �&     �&     �&  0   �&  ;   "'  9   ^'  &  �'     �+     �+     �+     �+     �+     �+     �+     �+     �+     ,     ",     ;,     U,     o,     �,     �,     �,     �,     �,             c   =       7   r   ]   2   ;           @   #       o           d   .   j   I   {   (   �   i           s   �                        
      �          z                   �   �   �   V   F           J           k       q       �          /       $   W   ^   �   H   p   �   R               f       )   *       �       [   �   0   �   '   D       P   ?      1   t   `   S       \   M   B   �       Z   �   3               �               &   -           >       �   5   u   X   Y                      n   |   E       a           �   ~   �   �   G           U                              ,   y       8   x           !   "   �   	   e       %   �   }   w   O   �   N       �   �       �   b   g       K       L           A   �   Q   T   h   :   �   �   6   �   +   <               v       l       �   m       �   �   �       C   9   _       4   �   �    % %01 %02 %03 %04 %05 %06 %07 %08 %09 %10 %11 %12 %Q1 %Q2 %Q3 %Q4 (RIF: ) - / 01 02 03 04 05 06 07 08 09 10 11 12 Abr Add summary at bottom Ago CSV file CSV file name Can't import data to document when state <> "draft" Col Company Company ref # Database Database name Datos mensuales Datos trimestrales Decimals in report Destination DB name Dic Digits Document number Ene Error ! Partner's VAT must be a unique value or empty Error ! The partner already has an invoice address. Error ! The partner does not have an invoice address. Error en tipo de ajuste Error! Feb File name From Host Import Importar Pedido Importar ajustes de entrada Importar datos desde ajuste de entradaa Importar datos desde factura de compra Importar datos desde pedido Importar factura de compra Importar lista de Pedidos Indique el cliente para la factura Indique el proveedor para la factura Invoice Invoice number Jul Jun Line Lines Load Load data from csv Load data wizard Load external data Loaded Mar May Must select an extarnal database related with ' +
                      'partner (%s %s) Name No se encontraron lineas, debe indicar un producto No se encontraron lineas, debe indicar un producto para %s No se encontró el producto: %s No se encontró el proveedor para la factura: %s None Nov Oct Order Reference must be unique ! Origin DB name Page Partner Password Pct type Please connect VPN to origin database prior to load data. Porcentajes mensuales Print Process Product Producto para la factura sin detalle (Documentos de compra) Profit DB Profit database settings Profit document # Profit import tools Profit invoice # Profit: SQL Server communication error Purchase Order Q1 Q2 Q3 Q4 Range: Related partners - Annual summary of sales Related partners - Sales (Amount) Related partners - Sales (Global quantity) Related partners - Sales (Slab quantity) Related partners - Sales (Tile quantity) Related partners - Summary of sales  Remove zero Row Sales Order Select a file to load Sep Server ip or name Show monthlys values Show monthlys values in report Show pct values Show pct values in report Show quarters values Show quarters values in report Summary TXT file Tecvemar - Profit import Tecvemar - Tools for document imports The Document you have been entering for this Partner has already been recorded The Number you have been entering for this Partner has already been recorded The VAT [%s] looks like '%value + 
                                            '[%s] which is'%rp.vat.upper()+
                                            ' already being used by: %s'%rp.name.upper())
                                }
                   }
        else:
            return super(res_partner,self).vat_change(cr, uid, ids, value, context=context)

    def check_vat_ve(self, vat, context = None):
        '
        Check Venezuelan VAT number, locally caled RIF.
        RIF: JXXXXXXXXX RIF CEDULA VENEZOLANO: VXXXXXXXXX CEDULA EXTRANJERO: EXXXXXXXXX
        '
        
        if context is None:
            context={}
        if re.search(r'^[VJEG][0-9]{9}$', vat):
            context.update({'ci_pas':False})
            return True
        if re.search(r'^([0-9]{1,8}|[D][0-9]{9})$', vat):
            context.update({'ci_pas':True})    
            return True
        return False
        
    def update_rif(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        su_obj = self.pool.get('seniat.url Title To Total Totals Type User Vat Error ! _Close tcv.base.import tcv.load.external.data tcv.profit.import.config tcv.profit.invoice.import tcv.purchase.order.import tcv.related.annual.sales tcv.related.annual.sales.lines tcv.sale.order.csv.import tcv.sale.order.import tcv.stock.picking.import tcv_related_annual_sales Project-Id-Version: OpenERP Server 6.0.4
Report-Msgid-Bugs-To: support@openerp.com
POT-Creation-Date: 2017-03-06 13:02+0000
PO-Revision-Date: 2017-03-06 13:02+0000
Last-Translator: <>
Language-Team: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 
Plural-Forms: 
 % %01 %02 %03 %04 %05 %06 %07 %08 %09 %10 %11 %12 %Q1 %Q2 %Q3 %Q4 (RIF: ) - / 01 02 03 04 05 06 07 08 09 10 11 12 Abr Add summary at bottom Ago Archivo CSV Nombre archivo CSV Imposible importar datos del documento cuando el estado <> "Borrador" Col Compania # ref. Compania Database Nombre Database Datos mensuales Datos trimestrales Decimales en reporte Nombre DB destino Dic Digitos Document number Ene Error ! Partner's VAT must be a unique value or empty Error ! La empresa ya posee una direccion de facturacion. Error ! La empresa no tiene una direccion de facturacion. Error en tipo de ajuste Error! Feb Nombre archivo Desde Servidor Importar Importar Pedido Importar ajustes de entrada Importar datos desde ajuste de entradaa Importar datos desde factura de compra Importar datos desde pedido Importar factura de compra Importar lista de Pedidos Indique el cliente para la factura Indique el proveedor para la factura Factura Numero factura Jul Jun Linea Lines Cargar Cargar datos desde csv Load data wizard Load external data Cargado Mar May Must select an extarnal database related with ' +
                      'partner (%s %s) Name No se encontraron lineas, debe indicar un producto No se encontraron lineas, debe indicar un producto para %s No se encontró el producto: %s No se encontró el proveedor para la factura: %s None Nov Oct ¡La referencia de la órden debe ser única! Origin DB name Pagina Empresa Password Tipo % Please connect VPN to origin database prior to load data. Porcentajes mensuales Imprimir Procesar Producto Producto para la factura sin detalle (Documentos de compra) Profit DB Opciones DB Profit Documento profit # Herramientas de importacion Profit Profit invoice # Profit: Error en comunicacion a SQL Server Pedido de compra Q1 Q2 Q3 Q4 Rango: Empresas relacionada - Sumatoria anual de ventas Empresas relacionada - Ventas (Monto) Empresas relacionada - Ventas (Cantidad global) Empresas relacionada - Ventas (Cantidad laminas) EMpresas relacionada - Ventas (Cantidad baldosas) EMpresas relacionada - Sumatoria de ventas  Remover ceros Fila Pedido de venta Selecciona un archivo para cargar Sep IP de servidor o nombre Mostrar valores mensuales Mostrar valores mensuales en reporte Mostrar valores % Mostrar valores % en reporte Mostrar valores trimestrales Mostrar valores trimestrales en reporte Sumatoria Archivo TXT Tecvemar - Profit import Tecvemar - Herramientas para importar documentos El documento indicado ya está registrado para esta empresa El número indicado para esta empresa ya está registrado The VAT [%s] looks like '%value + 
                                            '[%s] which is'%rp.vat.upper()+
                                            ' already being used by: %s'%rp.name.upper())
                                }
                   }
        else:
            return super(res_partner,self).vat_change(cr, uid, ids, value, context=context)

    def check_vat_ve(self, vat, context = None):
        '
        Check Venezuelan VAT number, locally caled RIF.
        RIF: JXXXXXXXXX RIF CEDULA VENEZOLANO: VXXXXXXXXX CEDULA EXTRANJERO: EXXXXXXXXX
        '
        
        if context is None:
            context={}
        if re.search(r'^[VJEG][0-9]{9}$', vat):
            context.update({'ci_pas':False})
            return True
        if re.search(r'^([0-9]{1,8}|[D][0-9]{9})$', vat):
            context.update({'ci_pas':True})    
            return True
        return False
        
    def update_rif(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        su_obj = self.pool.get('seniat.url Baldosa Hasta Total Totales Tipo Usuario Vat Error ! _Close tcv.base.import tcv.load.external.data tcv.profit.import.config tcv.profit.invoice.import tcv.purchase.order.import tcv.related.annual.sales tcv.related.annual.sales.lines tcv.sale.order.csv.import tcv.sale.order.import tcv.stock.picking.import tcv_related_annual_sales 
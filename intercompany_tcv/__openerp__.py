
#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

{
    "name" : "sales_intercompany",
    "version" : "0.2",
    "author" : "Jose",
    "website" : "http://vauxoo.com",
    "category": 'Generic Modules/Accounting',
    "description": """
    """,
    'init_xml': [],
    "depends" : ["sale","purchase","multi_company","stock","account"],
    'update_xml': [
                    #~ "workflow/purchase_workflow.xml",
                    #~ "workflow/sale_workflow.xml",
                    #~ "view/intercompany_transactions_user.xml",
                    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}


# -*- coding: utf-8 -*-
{
    'name': "Modulo Prueba",

    'summary': """
        modulo de prueba para la creacion de un modulo en odoo""",

    'description': """
        Es un modulo de prueba para la creacion de un modulo en odoo
    """,

    'author': "Test",
    'website': "consultor4",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.8',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
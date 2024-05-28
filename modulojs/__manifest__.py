# -*- coding: utf-8 -*-
{
    'name': 'Mi Modulo',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
        'views/mi_modelo_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'modulojs/static/src/js/contador_caracteres_widget.js',
            'modulojs/static/src/xml/mi_modelo_views.xml',
        ],
    },
}

# Copyright 2021 Vauxoo
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'HN Localization',
    'summary': '''
    HN Localization Modules
    ''',
    'author': 'IT Solutions,Vauxoo',
    'website': 'https://www.vauxoo.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations/EDI',
    'version': '15.0.1.0.1',
    'depends': [
        'l10n_hn',
        'l10n_latam_invoice_document',
        'account',
        'account_debit_note',
    ],
    'test': [
    ],
    'data': [
        'security/whtax_security.xml',
        'security/ir.model.access.csv',
        'data/l10n_latam.document.type.csv',
        #'data/res_country_state.xml',
        'data/res_bank.xml',
        'data/report_paperformat_data.xml',
        'data/l10n_hn_chart_data.xml',
        'data/account.group.csv',
        #'data/account.account.template.csv',
        #'data/l10n_hn_chart_post_data.xml',
        'data/data.xml',
        'views/res_group.xml',
        'views/account_move.xml',
        'views/account_journal_view.xml',
        'views/ir_sequence_view.xml',
        'views/l10n_hn_edi_cai_view.xml',
        'data/account_tax_group_data.xml',
        #'data/account_tax_data.xml',
        'views/withholding_view.xml',
        'views/whtax_report_view.xml',
        'views/report_invoice.xml',
        'report/whtax_report.xml',
        'report/report_whtax_template.xml',
    ],
    'demo': [
        'demo/l10n_hn_edi_cai_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_hn_edi/static/src/components/account_withholding_field/account_withholding_field.js',
            'l10n_hn_edi/static/src/components/account_withholding_field/account_withholding.xml'
        ]
    },
    'installable': True,
    'auto_install': False,
}

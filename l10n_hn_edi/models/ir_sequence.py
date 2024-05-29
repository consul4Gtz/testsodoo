from odoo import models, fields


class SecuenciaFiscal(models.Model):
    _inherit = 'ir.sequence'

    l10n_hn_edi_cai_id = fields.Many2one('l10n_hn_edi.cai', 'CAI', copy=False, ondelete='restrict',
                                         help='CAI used when the invoice was posted.')
    l10n_hn_min_range_number = fields.Integer('Initial Range', help='Indicates initial number for the CAI related.')
    l10n_hn_max_range_number = fields.Integer('Final Range', help='Indicates final number for the CAI related.')

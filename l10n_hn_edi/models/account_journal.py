from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_hn_edi_fe_seq_id = fields.Many2one(
        'ir.sequence', string='Electronic Invoice Sequence', copy=False, domain=[('l10n_hn_edi_cai_id', '!=', False)],
        help='This field contains the information related to the numbering of the Electronic Invoice for this '
        'journal.')
    l10n_hn_edi_nc_seq_id = fields.Many2one(
        'ir.sequence', string='Credit Note Sequence', copy=False, domain=[('l10n_hn_edi_cai_id', '!=', False)],
        help='This field contains the information related to the numbering of the electronic credit note of this '
        'journal.')
    l10n_hn_edi_nd_seq_id = fields.Many2one(
        'ir.sequence', string='Debit Note Sequence', copy=False, domain=[('l10n_hn_edi_cai_id', '!=', False)],
        help='This field contains the information related to the numbering of the journal entries of this journal.')
    l10n_hn_edi_wh_seq_id = fields.Many2one(
        'ir.sequence', string='Withholding Sequence', copy=False, domain=[('l10n_hn_edi_cai_id', '!=', False)],
        help='This field contains the information related to the numbering of the journal entries of this journal.')
    l10n_hn_address_issued_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('type', '=', 'invoice')]",
        string="Address Issued",
        help='Used in multiple-offices environments to show the given address in the PDF. If empty, the company '
        'address will be used.')

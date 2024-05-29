from odoo import models, fields


class L10nLatamDocumentType(models.Model):
    _inherit = 'l10n_latam.document.type'

    internal_type = fields.Selection(
        selection_add=[
            ('invoice', 'Invoices'),
            ('debit_note', 'Debit Notes'),
            ('credit_note', 'Credit Notes')])

    def _get_document_sequence_vals(self, journal):
        values = super()._get_document_sequence_vals(journal)
        if self.country_id != self.env.ref('base.hn'):
            return values
        values.update({
            'padding': 8,
            'implementation': 'no_gap',
            'l10n_latam_document_type_id': self.id,
            'prefix': None
        })
        return values

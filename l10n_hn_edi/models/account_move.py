from datetime import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_date = fields.Date()
    l10n_hn_edi_cai_id = fields.Many2one('l10n_hn_edi.cai', 'CAI', copy=False, tracking=True, ondelete='restrict',
                                         help='CAI used when the invoice was posted.')
    l10n_hn_edi_sequence_id = fields.Many2one('ir.sequence', help='Sequence used on the invoice validation.')
    l10n_hn_edi_sag = fields.Char('Sag Register')
    l10n_hn_edi_exempt_order = fields.Char('Exempt Order')
    l10n_hn_edi_exempt_certificate = fields.Char('Exempt Certificate')
    l10n_hn_edi_diplomatic = fields.Char('Carnet de Diplomatico')
    l10n_latam_document_type_id_code = fields.Char(related='l10n_latam_document_type_id.code', string='Doc Type')
    l10n_latam_internal_type = fields.Selection(
        related='l10n_latam_document_type_id.internal_type', string='L10n Latam Internal Type')
    l10n_hn_edi_temp_sequence = fields.Integer(
        string='Temporary sequence',
        help="Temporary sequence taken from ir.sequence related to document type. ", default=0, copy=False)
    l10n_latam_withholding_id = fields.Many2one('account.withholding', 'Withholding', copy=False, readonly=True,
                                                states={'draft': [('readonly', False)]})

    def action_post(self):
        posted_before = self.read(['posted_before'])
        result = super().action_post()
        for move in self.filtered(lambda m: m.journal_id.l10n_latam_use_documents and m.country_code == 'HN' and
                                  m.move_type in ['out_invoice', 'out_refund']):
            record_posted_before = False
            for record in posted_before:
                if record.get('id') == move.id:
                    record_posted_before = record.get('posted_before')
                    continue
            # Increase sequence number for specific document type
            if not record_posted_before:
                doc_type = move.l10n_hn_edi_get_doc_type()
                sequence = move.l10n_hn_edi_get_sequence_by_doc_type(doc_type)
                if not sequence:
                    continue
                sequence.next_by_id()
        return result

    def _post(self, soft=True):
        moves = self.filtered(lambda m: m.journal_id.l10n_latam_use_documents and m.country_code == 'HN' and
                              m.move_type in ['out_invoice', 'out_refund'])
        for move in moves:
            if move.l10n_latam_document_type_id and move.l10n_hn_edi_resequence_is_required():
                move.name = move._l10n_hn_edi_set_next_sequence()
        result = super()._post(soft=soft)
        for move in moves:
            doc_type = move.l10n_hn_edi_get_doc_type()
            sequence = move.l10n_hn_edi_get_sequence_by_doc_type(doc_type)
            if not sequence:
                continue
            move._l10n_hn_edi_validations(sequence)
            move.l10n_hn_edi_cai_id = sequence.l10n_hn_edi_cai_id
            move.l10n_hn_edi_sequence_id = sequence
        return result

    def _l10n_hn_edi_validations(self, sequence):
        self.ensure_one()
        if sequence.l10n_hn_edi_cai_id.authorization_end_date < self.invoice_date:
            raise UserError(_('Fiscal date expired %s') % sequence.l10n_hn_edi_cai_id.authorization_end_date)
        if sequence.l10n_hn_edi_cai_id.authorization_date > self.invoice_date:
            raise UserError(_('Fiscal date expired %s ') % (sequence.l10n_hn_edi_cai_id.authorization_date))
        if sequence.l10n_hn_max_range_number < sequence.number_next_actual:
            raise UserError(_('Fiscal correlative expired %s') % sequence.l10n_hn_max_range_number)
        if sequence.number_next_actual < sequence.l10n_hn_min_range_number:
            raise UserError(_('Fiscal correlative expired %s ') % (sequence.l10n_hn_min_range_number))

    def l10n_hn_edi_is_required(self):
        self.ensure_one()
        return self.company_id.country_id == self.env.ref('base.hn') and self.journal_id.l10n_latam_use_documents

    def l10n_hn_edi_resequence_is_required(self):
        self.ensure_one()
        if self.posted_before:
            return False
        return True

    def l10n_hn_edi_get_doc_type(self):
        if self.move_type in ['out_refund']:
            return '06'
        if not self.l10n_latam_document_type_id and self.move_type in ['out_refund','out_invoice']:
            raise ValidationError(_(
                'The eInvoicing document type is required. Please check your invoice settings.'))
        return self.l10n_latam_document_type_id.doc_code_prefix

    def l10n_hn_edi_get_sequence_by_doc_type(self, doc_type="01"):
        journal = self.journal_id
        return {
            '01': journal.l10n_hn_edi_fe_seq_id,
            '06': journal.l10n_hn_edi_nc_seq_id,
            '07': journal.l10n_hn_edi_nd_seq_id,
        }.get(doc_type)

    # -------------------------------------------------------------------------
    # SEQUENCE HACK
    # -------------------------------------------------------------------------

    def _get_last_sequence_domain(self, relaxed=False):
        # OVERRIDE
        where_string, param = super()._get_last_sequence_domain(relaxed)
        if self.l10n_hn_edi_is_required():
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param

    def _l10n_hn_edi_set_next_sequence(self):
        if self.l10n_hn_edi_is_required() and self.l10n_latam_document_type_id:
            doc_type = self.l10n_hn_edi_get_doc_type()
            sequence_id = self.l10n_hn_edi_get_sequence_by_doc_type(doc_type)
            return "%s%s-%s" % (
                sequence_id.prefix,
                doc_type,
                str(sequence_id.number_next_actual).zfill(sequence_id.padding),
            )
        return ""

    def _get_starting_sequence(self):
        # OVERRIDE
        if self.l10n_hn_edi_is_required() and self.l10n_latam_document_type_id:
            return self._l10n_hn_edi_set_next_sequence()
        return super()._get_starting_sequence()

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        # OVERRIDE
        hn_records = self.filtered(lambda i: i.l10n_latam_document_type_id and i.l10n_hn_edi_is_required())
        result = super(AccountMove, self - hn_records)._inverse_l10n_latam_document_number()
        for rec in hn_records:
            l10n_latam_document_number = rec._l10n_hn_edi_set_next_sequence()
            if rec.l10n_hn_edi_resequence_is_required() and\
                    rec.l10n_latam_document_number != l10n_latam_document_number:
                rec.l10n_latam_document_number = l10n_latam_document_number
                rec.name = l10n_latam_document_number
        return result

    def _get_sequence_format_param(self, previous):
        # OVERRIDE
        if not self or not self.l10n_hn_edi_is_required() or not self.l10n_latam_document_type_id:
            return super()._get_sequence_format_param(previous)

        doc_type = self.l10n_hn_edi_get_doc_type()
        sequence_id = self.l10n_hn_edi_get_sequence_by_doc_type(doc_type)
        if not self.l10n_hn_edi_temp_sequence or self.l10n_hn_edi_temp_sequence < sequence_id.number_next_actual:
            self.l10n_hn_edi_temp_sequence = sequence_id.number_next_actual

        format_values = {
            'prefix1': f'{sequence_id.prefix}{doc_type}-' if sequence_id.prefix else f'{doc_type}',
            'seq': self.l10n_hn_edi_temp_sequence,
            'suffix': '',
            'seq_length': sequence_id.padding,
            'year_length': 0,
            'year': 0,
            'month': 0,
            'year_end': 0,
            'year_end_length': 0,
        }
        return '{prefix1}{seq:0{seq_length}d}{suffix}', format_values

    @api.model
    def _l10n_hn_edi_cfdi_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words hn format for invoices
        :rtype: str
        """
        self.ensure_one()
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(self.amount_total)
        return '%(words)s ***' % {
            'words': words,
        }

    def _reverse_moves(self, default_values_list=None, cancel=False):
        res = super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        if not cancel:
            return res
        for move in res:
            # Increase sequence number for specific document type
            doc_type = move.l10n_hn_edi_get_doc_type()
            # The '03' code is used to indicate the document is a credit note.
            if doc_type != '06':
                continue
            sequence_id = self.l10n_hn_edi_get_sequence_by_doc_type(doc_type)
            if sequence_id:
                sequence_id.next_by_id()
        return res

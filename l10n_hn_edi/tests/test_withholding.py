from datetime import timedelta

from odoo.addons.account_edi.tests.common import AccountEdiTestCommon
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('hn_edi_withholding', 'post_install', '-at_install')
class TestHNWithholding(AccountEdiTestCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_hn.cuentas_plantilla', edi_format_ref=False):
        super().setUpClass(chart_template_ref=chart_template_ref, edi_format_ref=edi_format_ref)
        cls.company = cls.env.user.company_id
        cls.company.country_id = cls.env.ref('base.hn')
        cls.journal_general = cls.env['account.journal'].search([
            ('type', '=', 'general'), ('company_id', '=', cls.company.id)], limit=1)
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'), ('company_id', '=', cls.company.id)], limit=1)
        cls.journal_general.l10n_latam_use_documents = True
        cls.journal_general.l10n_hn_edi_wh_seq_id = cls.env.ref('l10n_hn_edi.sequence_withholding_000001')

        cls.partner = cls.env.ref('base.res_partner_2')
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': cls.journal.id,
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'invoice_line_ids': [0, 0, {
                'name': 'Line test',
                'quantity': 100.0,
                'price_unit': 100.0,
            }]
        })
        cls.withholding = cls.env['account.withholding']

    def test_withholding_flow(self):
        """Ensure that customer invoice flow is correct"""
        withholding = self._prepare_withholding()
        withholding.action_post()
        self.assertEqual(withholding.state, 'posted', 'Withholding not posted.')
        withholding.action_cancel()
        self.assertEqual(withholding.state, 'cancel', 'Withholding not cancelled.')
        withholding.action_draft()
        self.assertEqual(withholding.state, 'draft', 'Withholding not in draft.')

        report = self.env.ref('l10n_hn_edi.action_report_whtax', False)
        pdf_content, _content_type = report._render_qweb_pdf(withholding.id)
        self.assertTrue(pdf_content, 'Report not generated.')

    def test_cai_withholding_range(self):
        """Ensure that CAI ranges are corrects"""
        seq = self.journal_general.l10n_hn_edi_wh_seq_id
        cai = seq.l10n_hn_edi_cai_id
        seq.number_next_actual = 100
        withholding = self._prepare_withholding()
        date = withholding.date
        # end_date
        with self.assertRaises(UserError, msg="Cannot be validated with a date bigger than the correlative."):
            cai.authorization_end_date = date - timedelta(days=1)
            withholding.action_post()
        cai.authorization_end_date = date + timedelta(days=1)
        # start_date
        with self.assertRaises(UserError, msg="Cannot be validated with a date less than the correlative"):
            cai.authorization_date = date + timedelta(days=1)
            withholding.action_post()
        cai.authorization_date = date - timedelta(days=1)
        # max_number
        with self.assertRaises(UserError, msg="Cannot be validated with a date bigger than the correlative."):
            seq.l10n_hn_max_range_number = 99
            withholding.action_post()
        seq.l10n_hn_max_range_number = 110
        # min_number
        with self.assertRaises(UserError, msg="Cannot be validated with a date less than the correlative."):
            seq.l10n_hn_min_range_number = 101
            withholding.action_post()

    def _prepare_withholding(self):
        self.invoice.action_post()
        self.assertEqual(self.invoice.state, 'posted', 'Invoice not posted.')
        withholding_tax = self.env.ref('l10n_hn_edi.account_wtax_12_5').sudo()
        account = withholding_tax.invoice_repartition_line_ids.mapped('account_id').copy({
            'company_id': self.company.id})
        withholding_tax = withholding_tax.copy()
        withholding_tax.write({'company_id': self.company.id})
        (withholding_tax.invoice_repartition_line_ids | withholding_tax.refund_repartition_line_ids).write({
            'company_id': self.company.id, 'account_id': account.id,
        })
        withholding = self.withholding.create({
            'partner_id': self.partner.id,
            'journal_id': self.journal_general.id,
            'line_ids': [(0, 0, {
                'invoice_id': self.invoice.id,
                'wtax_id': withholding_tax.id,
            })]
        })
        withholding.line_ids.onchange_invoicewtax_id()
        withholding.line_ids.onchange_wtax_id()
        withholding.line_ids._onchange_wtax_amount()
        return withholding

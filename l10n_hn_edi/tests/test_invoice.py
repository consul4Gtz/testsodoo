from datetime import timedelta

from odoo.addons.account_edi.tests.common import AccountEdiTestCommon
from odoo.tests import tagged
from odoo.exceptions import UserError


@tagged('hn_edi', 'post_install', '-at_install')
class TestHNInvoice(AccountEdiTestCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_hn.cuentas_plantilla', edi_format_ref=False):
        super().setUpClass(chart_template_ref=chart_template_ref, edi_format_ref=edi_format_ref)
        cls.company = cls.env.user.company_id
        cls.company.country_id = cls.env.ref('base.hn')
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', cls.company.id)], limit=1)
        cls.journal.l10n_latam_use_documents = True
        cls.journal.l10n_hn_edi_fe_seq_id = cls.env.ref('l10n_hn_edi.sequence_electronic_invoice_0010001')
        cls.journal.l10n_hn_edi_nd_seq_id = cls.env.ref('l10n_hn_edi.sequence_debit_note_0010001')
        cls.journal.l10n_hn_edi_nc_seq_id = cls.env.ref('l10n_hn_edi.sequence_credit_note_0010001')

        cls.partner = cls.env.ref('base.res_partner_2')
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': cls.journal.id,
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'invoice_line_ids': [0, 0, {
                'name': 'Line test',
                'quantity': 100.0,
                'price_unit': 100.0,
            }]
        })

    def test_invoice_flow(self):
        """Ensure that customer invoice flow is correct"""
        self.invoice.l10n_latam_document_type_id = self.env.ref('l10n_hn_edi.sar_fact')
        self.invoice.action_post()
        seq_id = self.invoice.journal_id.l10n_hn_edi_fe_seq_id
        expected_number = "%s%s-%s" % (
            seq_id.prefix,
            self.invoice.l10n_hn_edi_get_doc_type(),
            str(seq_id.number_next_actual).zfill(seq_id.padding)
            )
        self.assertEqual(self.invoice.state, 'posted', 'Invoice not posted.')
        self.assertEqual(self.invoice.name, expected_number, 'Invoice name not assigned correctly.')
        report = self.env.ref('account.account_invoices_without_payment', False)
        pdf_content, _content_type = report._render_qweb_pdf(self.invoice.id)
        self.assertTrue(pdf_content, 'Report not generated.')

        # Test reset2draft process
        self.invoice.refresh()
        number = self.invoice.name
        self.invoice.button_draft()
        self.invoice.refresh()
        self.invoice.action_post()
        self.invoice.refresh()
        self.assertEqual(number, self.invoice.name, 'Invoice name updated on draft process.')

    def test_flow_with_several_draft_invoices(self):
        """Ensure that customer invoice flow and sequence number is correct when several draft invoices are created"""
        self.invoice.l10n_latam_document_type_id = self.env.ref('l10n_hn_edi.sar_fact')
        invoice_a = self.invoice.copy()
        invoice_b = self.invoice.copy()
        invoice_a.action_post()
        invoice_a.refresh()
        invoice_b.action_post()
        invoice_b.refresh()
        self.assertEqual(invoice_a.state, 'posted', 'Invoice not posted.')
        self.assertEqual(invoice_b.state, 'posted', 'Invoice not posted.')
        self.assertNotEqual(invoice_a.name, invoice_b.name, 'Invoice name were assigned correctly.')

    def test_out_invoice_create_refund(self):
        self.invoice.action_post()

        move_reversal = self.env['account.move.reversal'].with_context(
            active_model="account.move", active_ids=self.invoice.ids).create({
                'date': self.invoice.invoice_date,
                'reason': 'Testing reason',
                'refund_method': 'refund',
                'journal_id': self.invoice.journal_id.id
            })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])
        seq_id = reverse_move.journal_id.l10n_hn_edi_nc_seq_id
        expected_number = "%s%s-%s" % (
            seq_id.prefix,
            reverse_move.l10n_hn_edi_get_doc_type(),
            str(seq_id.number_next_actual).zfill(seq_id.padding)
            )
        reverse_move.action_post()
        self.assertEqual(reverse_move.move_type, "out_refund", "This invoice is not a customer refund")
        self.assertEqual(reverse_move.state, "posted", reverse_move.message_ids.mapped("body"))
        self.assertEqual(reverse_move.name, expected_number, "This invoice is not using the correct sequence")

    def test_cancel_refund(self):
        self.invoice.action_post()

        move_reversal = self.env['account.move.reversal'].with_context(
            active_model="account.move", active_ids=self.invoice.ids).create({
                'date': self.invoice.invoice_date,
                'reason': 'Testing reason',
                'refund_method': 'cancel',
                'journal_id': self.invoice.journal_id.id
            })
        reversal = move_reversal.reverse_moves()
        refund = self.env['account.move'].browse(reversal['res_id'])
        self.assertTrue(refund.l10n_hn_edi_cai_id, 'CAI data not assigned.')
        refund.refresh()
        new_refund = refund.copy()
        new_refund.action_post()
        self.assertEqual(new_refund.state, "posted", refund.message_ids.mapped("body"))

    def test_cai_invoice_range(self):
        """Ensure that CAI ranges are corrects"""
        seq = self.invoice.journal_id.l10n_hn_edi_fe_seq_id
        cai = seq.l10n_hn_edi_cai_id
        seq.number_next_actual = 100
        self.invoice.l10n_latam_document_type_id = self.env.ref('l10n_hn_edi.sar_fact')
        date = self.invoice.invoice_date
        # end_date
        with self.assertRaises(UserError, msg="Fiscal date expired"):
            cai.authorization_end_date = date - timedelta(days=1)
            self.invoice.action_post()
        cai.authorization_end_date = date + timedelta(days=1)
        # start_date
        with self.assertRaises(UserError, msg="Fiscal date expired"):
            cai.authorization_date = date + timedelta(days=1)
            self.invoice.action_post()
        cai.authorization_date = date - timedelta(days=1)
        # max_number
        with self.assertRaises(UserError, msg="Fiscal correlative expired"):
            seq.l10n_hn_max_range_number = 99
            self.invoice.action_post()
        seq.l10n_hn_max_range_number = 110
        # min_number
        with self.assertRaises(UserError, msg="Fiscal correlative expired"):
            seq.l10n_hn_min_range_number = 101
            self.invoice.action_post()

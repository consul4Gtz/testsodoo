import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountWithholding(models.Model):
    _name = 'account.withholding'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Withholding tax"
    _order = 'date desc, name desc, id desc'
    _mail_post_access = 'read'

    @api.model
    def _get_default_journal(self):
        journal_type = 'general'
        company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
        domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
        journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            error_msg = _('Please define an accounting miscellaneous journal in your company')
            raise UserError(error_msg)
        return journal

    def _get_default_currency(self):
        """ Get the default currency from either the journal, either the default journal's company. """
        journal = self._get_default_journal()
        return journal.currency_id or journal.company_id.currency_id

    @api.depends('line_ids.wtax_amount')
    def _compute_wtax_tamount(self):
        for rec in self:
            rec.wtax_tamount = sum([line.wtax_amount for line in rec.line_ids])

    company_id = fields.Many2one('res.company', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char('Number', required=True, readonly=True, copy=False, default='/')
    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True, states={'draft': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 string='Proveedor', change_default=True)
    ref = fields.Char("Reference", copy=False,)
    tax_id = fields.Char("NIF", related="partner_id.vat", store=True,)
    date = fields.Date(required=True, index=True, readonly=True, states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today)
    account_date = fields.Date(index=True, readonly=True, states={'draft': [('readonly', False)]},)
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('posted', 'Publicado'),
            ('cancel', 'Cancelado')
        ], required=True, readonly=True, copy=False, tracking=True, default='draft')
    journal_id = fields.Many2one('account.journal', readonly=True, states={'draft': [('readonly', False)]},
                                 domain="[('company_id', '=', company_id)]", default=_get_default_journal)
    user_id = fields.Many2one('res.users', copy=False, tracking=True, default=lambda self: self.env.user)
    company_currency_id = fields.Many2one(readonly=True, related='company_id.currency_id', string='Company Currency')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
                                  states={'draft': [('readonly', False)]}, string='Moneda',
                                  default=_get_default_currency)
    line_ids = fields.One2many('account.withholding.line', inverse_name='withholding_id', string='Bills',
                               copy=True, readonly=True, states={'draft': [('readonly', False)]})
    wtax_tamount = fields.Monetary('Withholding Total', currency_field='currency_id', store=True, readonly=True,
                                   compute='_compute_wtax_tamount')
    narration = fields.Text()
    move_count = fields.Integer(compute="_compute_moves", copy=False, default=0, store=True)
    move_ids = fields.Many2many('account.move', compute="_compute_moves", copy=False, store=True)
    #wtax_widget = fields.Text(compute='_compute_wtax_widget_info')
    wtax_widget = fields.Binary(compute='_compute_wtax_widget_info')
    # Sequence Data
    l10n_hn_edi_cai_id = fields.Many2one('l10n_hn_edi.cai', 'CAI', copy=False, tracking=True, ondelete='restrict',
                                         help='CAI used when the invoice was posted.')
    l10n_hn_edi_sequence_id = fields.Many2one('ir.sequence', help='Sequence used on the invoice validation.')

    def _compute_wtax_widget_info(self):
        for rec in self:
            rec.wtax_widget = False
            whtax_ids = rec.line_ids.mapped('wtax_id')
            lines = []
            for wtax in whtax_ids:
                monto = sum([line.wtax_amount for line in rec.line_ids.filtered(lambda r: r.wtax_id == wtax)])
                lines.append({'whtax': wtax, 'amount': monto})

            info = {'title': 'Resumen','content': []}
            currency_id = rec.currency_id

            if len(lines) != 0:
                for line in lines:
                    info['content'].append({
                        'whtax_name': line.get('whtax').name,
                        'amount': line.get('amount'),
                        'currency': currency_id.symbol,
                        'position': currency_id.position,
                        'digits': [69, currency_id.decimal_places],
                        'whtax_date': fields.Date.to_string(rec.account_date),
                    })
                info['title'] = "Resumen"
                rec.wtax_widget = info

    @api.depends('line_ids.move_id')
    def _compute_moves(self):
        for rec in self:
            moves = rec.mapped('line_ids.move_id')
            rec.move_ids = moves
            rec.move_count = len(moves)

    def _l10n_hn_edi_validations(self):
        self.ensure_one()
        if not self.journal_id:
            raise UserError(_("In order to allow validate the withholding is necessary assign a journal."))
        sequence = self.journal_id.l10n_hn_edi_wh_seq_id
        if not sequence:
            raise UserError(_("Please define a sequence for the withholding on the journal."))
        if sequence.l10n_hn_edi_cai_id:
            if sequence.l10n_hn_max_range_number < sequence.number_next_actual:
                raise UserError(_("Cannot be validated with a number bigger than the correlative."))
            if sequence.l10n_hn_min_range_number > sequence.number_next_actual:
                raise UserError(_("Cannot be validated with a number less than the correlative."))
            if self.date < sequence.l10n_hn_edi_cai_id.authorization_date:
                raise UserError(_("Cannot be validated with a date less than the correlative."))
            if self.date > sequence.l10n_hn_edi_cai_id.authorization_end_date:
                raise UserError(_("Cannot be validated with a date bigger than the correlative."))

    def action_post(self):
        for rec in self:
            rec._l10n_hn_edi_validations()
            rec.account_date = fields.Date.context_today(rec)
            rec.line_ids.mapped(lambda r: r.create_account_move())
            rec.state = 'posted'
            sequence = rec.journal_id.l10n_hn_edi_wh_seq_id.with_context(ir_sequence_date=rec.account_date)
            rec.name = sequence.next_by_id()
            rec.l10n_hn_edi_cai_id = sequence.l10n_hn_edi_cai_id
            rec.l10n_hn_edi_sequence_id = sequence

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec.line_ids.mapped(lambda r: r.move_id.sudo().button_draft())
            rec.line_ids.mapped(lambda r: r.move_id.sudo().with_context(force_delete=True).unlink())
            rec.line_ids.write({'base_amount': 0.0, 'wtax_amount': 0.0})

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'


class AccountWithholdingLine(models.Model):
    _name = "account.withholding.line"
    _description = "Withholding Item"
    _order = "date desc, withholding_name desc, id"
    _check_company_auto = True

    withholding_id = fields.Many2one('account.withholding', index=True, required=True, readonly=True, auto_join=True,
                                     ondelete="cascade", help="The Withholding line.")
    withholding_name = fields.Char(related='withholding_id.name', store=True, index=True)
    date = fields.Date(related='withholding_id.date', store=True, copy=False, group_operator='min')
    account_date = fields.Date(related='withholding_id.account_date', index=True, readonly=True, store=True,)
    ref = fields.Char(related='withholding_id.ref', store=True, copy=False, index=True, readonly=False)
    parent_state = fields.Selection(related='withholding_id.state', store=True, readonly=True)
    journal_id = fields.Many2one(related='withholding_id.journal_id', store=True, index=True, copy=False)
    company_id = fields.Many2one(related='withholding_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='invoice_id.currency_id', store=True,)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency', store=True)
    account_id = fields.Many2one('account.account', index=True, ondelete="restrict", check_company=True,
                                 domain=[('deprecated', '=', False)])
    invoice_id = fields.Many2one(comodel_name='account.move', required=True)
    invoice_name = fields.Char(related="invoice_id.name", string='#Factura', store=True)
    invoice_ref = fields.Char(related="invoice_id.ref", string='Referencia', store=True)
    base_amount = fields.Monetary(currency_field='currency_id')
    wtax_id = fields.Many2one('account.tax', string='Withholding Name', domain=[('type_tax_use', '=', 'none')])
    wtax_code = fields.Char(related="wtax_id.description", string='Withholding Code', store=True,)
    wtax_amount = fields.Monetary('Monto Retención', currency_field='currency_id', readonly=True,)
    wtax_rate = fields.Float('Withholding rate',)
    move_id = fields.Many2one(comodel_name='account.move', string='Asiento contable',)
    partner_id = fields.Many2one(related='withholding_id.partner_id', string='Supplier', store=True,)
    tax_id = fields.Char("NIF", related="partner_id.vat", store=True,)

    _sql_constraints = [
        ('wtax_invoice_uniq', 'unique (withholding_id, wtax_id, invoice_id, company_id)',
         'La retención y la factura debe ser único por documento de retención !'),
    ]

    @api.onchange('invoice_id')
    def onchange_invoicewtax_id(self):
        self.base_amount = self.invoice_id.amount_untaxed

    @api.onchange('wtax_id')
    def onchange_wtax_id(self):
        self.wtax_rate = self.wtax_id.amount
        self.account_id = self.wtax_id.invoice_repartition_line_ids.mapped('account_id')

    @api.onchange('wtax_rate', 'base_amount')
    def _onchange_wtax_amount(self):
        for line in self:
            line.update({'wtax_amount': self.base_amount * self.wtax_rate / 100})

    def _prepare_wtholding_moves(self):
        rec = self
        ref = '%s - %s' % (rec.wtax_id.name, rec.invoice_id.name)
        company_currency = rec.company_id.currency_id

        # Compute amounts.
        counterpart_amount = rec.wtax_amount

        # Manage currency.
        if rec.currency_id == company_currency:
            # Single-currency.
            balance = counterpart_amount
            #counterpart_amount = 0.0
            currency_id = False

        else:
            # Multi-currencies.
            balance = rec.currency_id._convert(counterpart_amount, company_currency, rec.company_id, rec.account_date)
            currency_id = rec.currency_id.id

        move_vals = {
            'date': fields.Date.context_today(rec),
            'ref': ref,
            'journal_id': rec.journal_id.id,
            'currency_id': rec.currency_id.id or rec.company_id.currency_id.id,
            'partner_id': rec.partner_id.id,
            'line_ids': [
                # Receivable / Payable / Transfer line.
                (0, 0, {
                    'name': ref,
                    'amount_currency': counterpart_amount if rec.currency_id.id else 0.0,
                    'currency_id': rec.currency_id.id,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'date_maturity': rec.withholding_id.account_date,
                    'partner_id': rec.invoice_id.partner_id.commercial_partner_id.id,
                    'account_id': rec.invoice_id.partner_id.commercial_partner_id.property_account_payable_id.id,
                }),
                # Retención.
                (0, 0, {
                    'name': ref,
                    'amount_currency': -counterpart_amount if rec.currency_id.id else 0.0,
                    'currency_id': rec.currency_id.id,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'date_maturity': rec.withholding_id.account_date,
                    'partner_id': rec.invoice_id.partner_id.commercial_partner_id.id,
                    'account_id': rec.account_id.id,
                }),
            ],
        }
        return move_vals

    def create_account_move(self):
        for rec in self:
            # se crea el encabezado del asiento
            move = self.env['account.move'].with_context(default_type='entry')
            rec.move_id = move.create(rec._prepare_wtholding_moves())
            rec.move_id.action_post()

            # se concilia
            destination_account_id = rec.invoice_id.partner_id.commercial_partner_id.property_account_payable_id
            if rec.invoice_id:
                # (rec.move_id | rec.invoice_id).line_ids.filtered(
                #     lambda line: not line.reconciled and line.account_id == destination_account_id and not (
                #         line.account_id == line.payment_id.writeoff_account_id and
                #         line.name == line.payment_id.writeoff_label)).reconcile()
                (rec.move_id | rec.invoice_id).line_ids.filtered(
                    lambda line: not line.reconciled and line.account_id == destination_account_id).reconcile()
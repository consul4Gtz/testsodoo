from odoo.osv import expression
from odoo import api, fields, models


class L10nHNEdiCAI(models.Model):
    _name = 'l10n_hn_edi.cai'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Allow manage the CAI for the company.'

    name = fields.Char('CAI', help='Indicates the CAI number.', required=True, tracking=True)
    code = fields.Char(index=True, tracking=True, help='Code used to identify this record.')
    authorization_date = fields.Date('Expedition Date', required=True, tracking=True,
                                     help='Expedition date of the CAI document.')
    authorization_end_date = fields.Date('Final Date', required=True, tracking=True,
                                         help='Indicates the final date for this record.')
    active = fields.Boolean(tracking=True, default=True)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    sequence_ids = fields.One2many('ir.sequence', 'l10n_hn_edi_cai_id')

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the CAI must be unique per company !'),
        ('name_company_uniq', 'unique (name,company_id)', 'The CAI must be unique per company !')
    ]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        result = []
        for cai in self:
            if cai.code:
                name = '[%s] %s' % (cai.code, cai.name)
                result.append((cai.id, name))
                continue
            result.append((cai.id, cai.name))
        return result

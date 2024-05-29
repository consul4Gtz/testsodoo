from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _localization_use_documents(self):
        """ Si base es Honduras, retorna True para usar documentos latinos """
        self.ensure_one()
        return self.country_id == self.env.ref('base.hn') or super()._localization_use_documents()

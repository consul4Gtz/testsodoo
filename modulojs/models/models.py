# -*- coding: utf-8 -*-
from odoo import models, fields


class MiModelo(models.Model):
    _name = 'mi_modulo.mi_modelo'
    _description = 'Mi Modelo'

    mi_campo = fields.Char(string="Mi Campo")

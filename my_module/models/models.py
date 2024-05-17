# -*- coding: utf-8 -*-

from odoo import models, fields, api
from unidecode import unidecode

class my_module(models.Model):
    _name = 'my_module.my_module'

    name = fields.Char("Nombre")
    description = fields.Text('Descripción')
    value = fields.Integer("Valor")
    value2 = fields.Float("Cantidad",compute="_value_pc", store=True)
    #cambios realizados 
    start_datetime = fields.Datetime('Tiempo inicial', default=lambda self: fields.Datetime.now())

    @api.model  
    def create(self, values):
        if 'name' in values:
            values['name'] = unidecode(values['name'])
            return super(my_module, self).create(values)
    def write(self, values):
        if 'name' in values:
            values['name'] = unidecode(values['name'])
            return super(my_module, self).write(values)
        
    @api.depends('value')
    def _value_pc(self):
        self.value2 = float(self.value) / 100
# -*- coding: utf-8 -*-


from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"
    
    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('date_order')
    def _get_start_month(self):
        for rec in self:
            if rec.date_order:
                rec.start_month = rec.date_order.month

    def process_month(self):
        accounts = self.env['purchase.order'].search([])
        for i in accounts:
            if i.date_order:
                month = int(i.date_order.month)
                sql = """UPDATE purchase_order SET start_month = %s WHERE id = %s""" %(month,i.id)
                self.env.cr.execute(sql)

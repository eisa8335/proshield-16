# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = "res.partner"

    area = fields.Char(string="Area")
    area_id = fields.Many2one('area.area', string="Area..")
    premise_type_id = fields.Many2one('premise.type', string="Premise Type..")
    premise_categ_id = fields.Many2one('premise.category', string="Premise Category")
    job_count = fields.Integer(string="Jobs Count", compute="_get_job_count")
    contract_count = fields.Integer(string="Contract Count", compute="_get_contract_count")
    client_source_id = fields.Many2one('client.source', string="Client Source")

    def open_contracts(self):
        partner_id = self.id
        domain = [('partner_id', '=', partner_id)]
        context = {'default_partner_id': partner_id}
        return {
            'name': _('Contracts'),
            'domain': domain,
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.contract',
            'type': 'ir.actions.act_window',
        }

    def _get_contract_count(self):
        partner_id = self.id
        obj_pool = self.env['service.contract'].search_count([('partner_id', '=', partner_id)])
        self.contract_count = obj_pool

    def _get_job_count(self):
        partner_id = self.id
        obj_pool = self.env['calendar.event'].search_count([('partner_id', '=', partner_id)])
        self.job_count = obj_pool

    def open_jobs(self):
        partner_id = self.id
        domain = [('partner_id', '=', partner_id)]
        context = {'default_partner_id': partner_id}
        return {
            'name': _('Jobs'),
            'domain': domain,
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'calendar.event',
            'type': 'ir.actions.act_window',
        }

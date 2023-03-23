# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class TeamScheduling(models.Model):
    _name = "team.scheduling"
    _description = 'Team Scheduling'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, translate=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    start_date = fields.Datetime(string="Start Date & Time", default=fields.Datetime.now, required=True)
    end_date = fields.Datetime(string="End Date & Time", required=True)
    service_type = fields.Char(string="Service Type")
    service_team = fields.Many2one('service.team', string="Team")
    amount = fields.Float(string="Amount")
    remarks = fields.Text(string="Remarks", translate=True)
    state = fields.Selection([
        ('draft', 'New'),
        ('reschedule', 'Rescheduled'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, default='draft')

    def cancel_task(self):
        self.write({'state': 'cancel'})

    def reschedule_task(self):
        self.write({'state': 'reschedule'})

    def complete_task(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'team.collection',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_name': self.id},
            'target': 'new',
        }


class TeamCollection(models.TransientModel):
    _name = "team.collection"

    name = fields.Char(string='Job No', required=True, translate=True)
    amount_received = fields.Float(string='Amount', translate=True)
    payment_type = fields.Selection([
        ('cash', 'Cash'),
        ('cheque', 'Cheque')], string='Payment Type', translate=True)
    bank_name = fields.Char(string='Bank Name', translate=True)
    cheque_no = fields.Char(string='Cheque No', translate=True)
    invice_no = fields.Many2one('account.move', string='Invoice No')

    def action_submit(self):
        team_scheduling = self.env['team.scheduling'].browse(self._context.get('active_ids', []))
        if team_scheduling:
            team_scheduling.write({'state': 'done'})

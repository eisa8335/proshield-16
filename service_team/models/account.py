# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    service_team_id = fields.Many2one('service.team', string='Service Team')
    job_id = fields.Many2one('calendar.event', string='Job', readonly=True)
    job_date = fields.Date(string="Job Date", readonly=True)
    job_card = fields.Char(string="Job Card#", readonly=True)
    job_type_id = fields.Many2one('job.type', string="Job Type")
    contract_id = fields.Many2one('service.contract', string="Contract Ref")
    internal_ref = fields.Text(string="Internal Ref")
    next_execution_date = fields.Date(string="Next Execution Date")
    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('invoice_date')
    def _get_start_month(self):
        for rec in self:
            if rec.invoice_date:
                rec.start_month = rec.invoice_date.month
            else:
                rec.start_month = 0

    def process_month(self):
        accounts = self.env['account.move'].search([('invoice_date', '!=', False)])
        for account in accounts:
            account.start_month = account.invoice_date.month

    @api.model
    def _cron_check_followup(self):
        # Find all open invoices that are overdue
        invoice_ids = self.env['account.move'].search(
            [('payment_state', '=', 'not_paid'), ('move_type', '=', 'out_invoice'), ('invoice_date_due', '<', fields.Date.today())])

        # Get the email template for overdue invoice follow-up mail
        template_id = self.env.ref('service_team.overdue_invoice_followup_mail_inherit')

        # Find all users/salespersons who have overdue invoices
        users_with_overdue_invoices = set(invoice_ids.mapped('user_id'))

        # Send email to each user/salesperson with their overdue invoices
        for user in users_with_overdue_invoices:
            invoices_for_user = invoice_ids.filtered(lambda inv: inv.user_id == user)
            if not invoices_for_user:
                continue

            invoice_due_detail_list = []
            count = 1
            for invoice in invoices_for_user:
                if not invoice.next_execution_date:
                    next_execution_date = invoice.invoice_date_due + relativedelta(days=7)
                    invoice.write({'next_execution_date': next_execution_date})
                else:
                    next_execution_date = invoice.next_execution_date

                date_after_seven_days = next_execution_date + relativedelta(days=7)
                date_after_7_days = date_after_seven_days.date()
                if date_after_7_days != fields.Date.today():
                    continue

                invoice_due_detail = {
                    'serial': count,
                    'number': invoice.number,
                    'partner_id': invoice.partner_id.name,
                    'date': invoice.invoice_date,
                    'due_date': invoice.invoice_date_due,
                    'amount': invoice.residual,
                }
                count += 1
                invoice_due_detail_list.append(invoice_due_detail)

            if not invoice_due_detail_list:
                continue

            # Update the email template with overdue invoice details and send email to the user
            template = template_id.with_context({'invoice_list': invoice_due_detail_list})
            if user.partner_id.email:
                template.email_to = user.partner_id.email
            template.send_mail(invoice_id.id, force_send=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('date')
    def _get_start_month(self):
        for rec in self:
            if rec.date:
                rec.start_month = rec.date.month
            else:
                rec.start_month = 0

    def process_month(self):
        payments = self.env['account.payment'].search([('date', '!=', False)])
        for payment in payments:
            payment.start_month = payment.date.month


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('date')
    def _get_start_month(self):
        for rec in self:
            if rec.date:
                rec.start_month = rec.date.month
            else:
                rec.start_month = 0

    def process_month(self):
        # Get all account.move.line records
        account_move_lines = self.search([('date', '!=', False)])

        # Loop through each record and update start_month field
        for account_move_line in account_move_lines:
            start_month = datetime.strptime(account_move_line.date, '%Y-%m-%d').month
            account_move_line.start_month = start_month

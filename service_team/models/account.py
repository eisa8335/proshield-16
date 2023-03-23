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

    def process_month(self):
        accounts = self.env['account.move'].search([])
        for i in accounts:
            if i.date_invoice:
                month = int(datetime.strptime(i.date_invoice, '%Y-%m-%d').month)
                sql = """UPDATE account_move SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)

    @api.model
    def _cron_check_followup(self):
        invoice_ids = self.env['account.move'].search([('state', '=', 'open'), ('type', '=', 'out_invoice')])
        template_id = self.env.ref('service_team.overdue_invoice_followup_mail_inherit')
        today = datetime.now().date()
        salepersons_lst = []
        n = 1
        for each in invoice_ids:
            date_due = each.date_due
            date_due = datetime.strptime(date_due, "%Y-%m-%d")
            if date_due.date() < today:
                if not each.next_execution_date:
                    next_execution_date = each.date_due
                    date_after_seven_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(days=7)
                    date_after_7_days = date_after_seven_days.date()
                    if today == date_after_7_days:
                        if each.user_id.id not in salepersons_lst:
                            salepersons_lst.append(each.user_id.id)
                else:
                    next_execution_date = each.next_execution_date
                    date_after_seven_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(days=7)
                    date_after_7_days = date_after_seven_days.date()
                    if today == date_after_7_days:
                        if each.user_id.id not in salepersons_lst:
                            salepersons_lst.append(each.user_id.id)
                n += 1

        for each in salepersons_lst:
            invoice_due_detail_list = []
            count = 1
            for invoice_id in invoice_ids.filtered(lambda l: l.user_id.id == each):
                if datetime.strptime(invoice_id.date_due, "%Y-%m-%d").date() < today:
                    if not invoice_id.next_execution_date:
                        next_execution_date = invoice_id.date_due
                        date_after_seven_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(
                            days=7)
                        date_after_7_days = date_after_seven_days.date()
                    else:
                        next_execution_date = invoice_id.next_execution_date
                        date_after_seven_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(
                            days=7)
                        date_after_7_days = date_after_seven_days.date()
                    if today == date_after_7_days:
                        invoice_due_detail = {}
                        invoice_due_detail['serial'] = count
                        invoice_due_detail['number'] = invoice_id.number
                        invoice_due_detail['partner_id'] = invoice_id.partner_id.name
                        invoice_due_detail['date'] = invoice_id.date_invoice
                        invoice_due_detail['due_date'] = invoice_id.date_due
                        invoice_due_detail['amount'] = invoice_id.residual
                        count += 1
                        invoice_due_detail_list.append(invoice_due_detail)
                        invoice_id.write({'next_execution_date': date_after_7_days})
            if salepersons_lst:
                user_id = self.env['res.users'].browse(each)
                if user_id.partner_id.email:
                    template_id.email_to = user_id.partner_id.email
                if template_id:
                    template_id.with_context({'invoice_list': invoice_due_detail_list}).send_mail(invoice_id.id,
                                                                                                  force_send=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('date')
    def _get_start_month(self):
        for rec in self:
            if rec.date:
                rec.start_month = rec.date.month

    def process_month(self):
        accounts = self.env['account.payment'].search([])
        for i in accounts:
            if i.date:
                month = i.date.month
                sql = """UPDATE account_payment SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)


# class AccountMove(models.Model):
#     _inherit = "account.move"
#
#     start_month = fields.Integer(compute='_get_start_month', store=True)
#
#     @api.one
#     @api.depends('date')
#     def _get_start_month(self):
#         if self.date:
#             self.start_month = int(datetime.strptime(self.date, '%Y-%m-%d').month)
#
#     @api.model
#     def process_month(self):
#         accounts = self.env['account.move'].search([])
#         for i in accounts:
#             if i.date:
#                 month = int(datetime.strptime(i.date, '%Y-%m-%d').month)
#                 sql = """UPDATE account_move SET start_month = %s WHERE id = %s""" % (month, i.id)
#                 self.env.cr.execute(sql)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    start_month = fields.Integer(compute='_get_start_month', store=True)

    @api.depends('date')
    def _get_start_month(self):
        for rec in self:
            if rec.date:
                rec.start_month = rec.date.month

    def process_month(self):
        accounts = self.env['account.move.line'].search([])
        for i in accounts:
            if i.date:
                month = int(datetime.strptime(i.date, '%Y-%m-%d').month)
                sql = """UPDATE account_move_line SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)

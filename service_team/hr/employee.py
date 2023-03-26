# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class EmployeeInherit(models.Model):
    _inherit = "hr.employee"

    passport_doc_no = fields.Char(string="Passport Doc Number")
    passport_issue_date = fields.Date(string="Passport Issue Date")
    passport_expiry_date = fields.Date(string="Passport Expiry Date")

    visa_doc_no = fields.Char(string="Visa Doc Number")
    visa_issue_date = fields.Date(string="Visa Issue Date")
    visa_expiry_date = fields.Date(string="Visa Expiry Date")

    eid_doc_no = fields.Char(string="Emirates ID  Number")
    eid_issue_date = fields.Date(string="Emirates ID Issue Date")
    eid_expiry_date = fields.Date(string="Emirates ID Expiry Date")

    health_card_no = fields.Char(string="Health Card Number")
    health_card_issue_date = fields.Date(string="Health Card Issue Date")
    health_card_expiry_date = fields.Date(string="Health Card Expiry Date")

    dm_card_no = fields.Char(string="DM Card Number")
    dm_card_issue_date = fields.Date(string="DM Issue Date")
    dm_card_expiry_date = fields.Date(string="DM Expiry Date")

    @api.model
    def _cron_check_followup(self):
        employee_ids = self.env['hr.employee'].search([])
        template_id = self.env.ref('service_team.hr_document_followup_mail_inherit')
        today = datetime.now().date()
        employee_details_lst = []
        count = 1
        for each in employee_ids:
            employee_details = {}
            if each.passport_expiry_date and (
                    each.passport_expiry_date - relativedelta(days=13)).date() == today:
                employee_details['passport_expiry_date'] = each.passport_expiry_date
            if each.visa_expiry_date and (
                    each.visa_expiry_date - relativedelta(days=13)).date() == today:
                employee_details['visa_expiry_date'] = each.visa_expiry_date
            if each.dm_card_expiry_date and (
                    each.dm_card_expiry_date - relativedelta(days=13)).date() == today:
                employee_details['dm_card_expiry_date'] = each.dm_card_expiry_date
            if each.eid_expiry_date and (
                    each.eid_expiry_date - relativedelta(days=13)).date() == today:
                employee_details['eid_expiry_date'] = each.eid_expiry_date
            if employee_details:
                employee_details['serial'] = count
                employee_details['name'] = each.name
                employee_details['number'] = each.employee_number
                count += 1
                employee_details_lst.append(employee_details)
        if employee_details_lst:
            if template_id:
                template_id.with_context({'employee_details_lst': employee_details_lst}).send_mail(each.id,
                                                                                                   force_send=True)

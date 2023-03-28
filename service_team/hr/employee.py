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
        # Get all employees
        employees = self.env['hr.employee'].search([])

        # Get the follow-up email template
        template = self.env.ref('service_team.hr_document_followup_mail_inherit')

        # Get today's date
        today = fields.Date.today()

        # Create a list of employees due for follow-up
        followup_employees = []
        for employee in employees:
            employee_followup = {}
            if employee.passport_expiry_date and (
                    employee.passport_expiry_date - relativedelta(days=13)).date() == today:
                employee_followup['passport_expiry_date'] = employee.passport_expiry_date
            if employee.visa_expiry_date and (employee.visa_expiry_date - relativedelta(days=13)).date() == today:
                employee_followup['visa_expiry_date'] = employee.visa_expiry_date
            if employee.dm_card_expiry_date and (employee.dm_card_expiry_date - relativedelta(days=13)).date() == today:
                employee_followup['dm_card_expiry_date'] = employee.dm_card_expiry_date
            if employee.eid_expiry_date and (employee.eid_expiry_date - relativedelta(days=13)).date() == today:
                employee_followup['eid_expiry_date'] = employee.eid_expiry_date
            if employee_followup:
                employee_followup['name'] = employee.name
                employee_followup['work_email'] = employee.work_email
                followup_employees.append(employee_followup)

        # Send the follow-up email for each employee
        for employee_followup in followup_employees:
            # Create a dictionary of employee details
            followup_details = {}
            for i, (key, value) in enumerate(employee_followup.items()):
                if key == 'name':
                    followup_details['name'] = value
                elif key == 'work_email':
                    continue
                else:
                    followup_details[key] = {
                        'expiry_date': value,
                        'serial': i + 1,
                    }

            # Send the follow-up email
            if followup_details:
                template.with_context({'employee_details': followup_details}).send_mail(
                    recipient_ids=[(0, 0, {'email': employee_followup['work_email']})],
                    force_send=True
                )

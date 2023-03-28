# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class ServiceQuotation(models.Model):
    _name = "service.quotation"
    _description = 'Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_warrant_selection(self):
        selection = [('0', 'No Warranty')]
        selection_ext = [(str(x), str(x) + ' Months') for x in range(1, 13)]
        selection.extend(selection_ext)
        return selection

    def _default_employee(self):
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    select_service = fields.Selection([('qps', 'Pest Control Service'), ('qds', 'Disinfection Service')],
                                      string="Choose Service", default='qps')
    product_id = fields.Many2one('product.product', string="Service Type")
    job_area_id = fields.Many2one('job.area', string="Area Covered", required=False)
    service_description = fields.Char(string="Service Description")
    job_type_id = fields.Many2one('job.type', string="Job Type")
    followup_visit = fields.Boolean(string="Follow Up Visit")
    followup_days = fields.Selection([(str(x), str(x) + ' Days') for x in range(1, 31)], string="Follow Up After")
    warranty = fields.Selection(get_warrant_selection, string="Warranty")
    name = fields.Char(string="Quotation Reference", readonly=True)
    residential = fields.Boolean(string="Residential")

    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    state = fields.Selection(
        [('valid', 'Valid'), ('expired', 'Expired'), ('approved', 'Approved'), ('cancelled', 'Cancelled'), ],
        string="Status", default='valid')
    contact_id = fields.Many2one('res.partner', string="Contact")
    date = fields.Date(string="Quotation Date", default=fields.Date.today)
    amount = fields.Float(string="Quotation Value", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    payment_term_id = fields.Many2one('service.payment.term', string="Payment Term", required=True)
    validity_id = fields.Many2one('service.validity', string="Validity", required=True)
    frequency_id = fields.Many2one('service.frequency', string="Frequency Of Treatment")
    scope_of_works = fields.Many2many('service.scope.work', 'rel_quotation_scope', 'quotation_id', 'scope_id',
                                      string="Scope Of Work")
    covered_pests = fields.Many2many('covered.pest', 'rel_quotation_pest', 'quotation_id', 'pest_id',
                                     string="Covered Pest")
    callback_id = fields.Many2one('service.callback', string="Callbacks", required=False)
    contractors_obligations = fields.Many2many('contract.obligation', 'rel_quotation_contra_oblig', 'quotation_id',
                                               'obligation_id', string="Contractor's Obligation", )
    client_obligations = fields.Many2many('client.obligation', 'rel_quotation_client_oblig', 'quotation_id',
                                          'clie_obliga_id', string="Client Obligation")
    covered_area = fields.Text(string="Covered Areas", required=True)
    remarks = fields.Text(string="Remarks")
    employee_id = fields.Many2one('hr.employee', string="Signed By", required=True, default=_default_employee)
    next_execution_date = fields.Date(string="Next Execution Date", default=fields.Date.today)
    start_month = fields.Integer(compute='_get_start_month', store=True)

    def approve(self):
        self.write({'state': 'approved'})

    def cancel(self):
        self.write({'state': 'cancelled'})

    def reinstate(self):
        self.write({'state': 'valid'})

    def refresh(self):
        self.get_expiry()

    def create_contract(self):
        scope_of_works = self.scope_of_works.ids
        covered_pests = self.covered_pests.ids
        contractors_obligations = self.contractors_obligations.ids
        client_obligations = self.client_obligations.ids

        contract_payment = self.env['service.payment.term'].search([], limit=1)
        product = self.env['product.product'].search([('type', '=', 'service')], limit=1)
        vals = {
            'partner_id': self.partner_id.id,
            'contact_id': self.contact_id.id,
            'date': self.date,
            'payment_term_id': self.payment_term_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'frequency_id': self.frequency_id.id,
            'callback_id': self.callback_id.id,
            'employee_id': self.employee_id.id,
            'covered_area': self.covered_area,
            'product_id': product.id,
            'date_start': fields.Date.today(),
            'contract_payment': contract_payment.id,
            'date_end': fields.Date.today(),
            'scope_of_works': [(6, 0, scope_of_works)],
            'covered_pests': [(6, 0, covered_pests)],
            'contractors_obligations': [(6, 0, contractors_obligations)],
            'client_obligations': [(6, 0, client_obligations)],
        }

        contract_pool = self.env['service.contract']
        contract = contract_pool.create(vals)

        return {
            "name": "Contract",
            "type": 'ir.actions.act_window',
            "view_type": 'form',
            "view_mode": 'form',
            'res_model': "service.contract",
            "res_id": contract.id,
            'target': 'new'
        }

    @api.model
    def _cron_check_expiry(self):
        contracts = self.search([('state', '!=', 'cancelled')])
        contracts.get_expiry()

    @api.model
    def _cron_check_followup(self):
        # Get all valid service quotations
        orders = self.env['service.quotation'].search([('state', '=', 'valid')])

        # Get the follow-up email template
        template = self.env.ref('service_quotation.service_quotation_followup_mail_inherit')

        # Get today's date
        today = fields.Date.today()

        # Group service quotations by employee
        orders_by_employee = {}
        for order in orders:
            employee_id = order.employee_id.id
            if employee_id not in orders_by_employee:
                orders_by_employee[employee_id] = []
            orders_by_employee[employee_id].append(order)

        # Send follow-up emails for each employee
        for employee_id, orders in orders_by_employee.items():
            # Get the employee's email address
            employee = self.env['hr.employee'].browse(employee_id)
            if not employee.work_email:
                continue

            # Get the service quotations due for follow-up
            followup_orders = []
            for order in orders:
                if order.next_execution_date:
                    followup_date = order.next_execution_date + relativedelta(days=7)
                    if followup_date.date() == today:
                        followup_orders.append(order)
                        order.write({'next_execution_date': followup_date.date()})

            # Create a dictionary of service quotation details
            followup_details = {}
            for i, order in enumerate(followup_orders):
                followup_details[order.id] = {
                    'serial': i + 1,
                    'name': order.name,
                    'partner': order.partner_id.name,
                    'date': order.date,
                    'amount': order.amount,
                }

            # Send the follow-up email
            if followup_details:
                template.with_context({'quotation_details': followup_details}).send_mail(followup_orders[0].id,force_send=True, email_values={'email_to': employee.work_email})

    def get_expiry(self):
        today = fields.Date.today()
        end_date = self.date
        validity = self.validity_id
        validity_days = validity.numbers
        # if not validity_days:
        #     raise ValidationError("No Validity Days Set on This Validity Term!")
        end_date = end_date + relativedelta(days=validity_days)
        delta = end_date - today
        days_remaining = delta.days
        state = self.state
        if state not in ('cancelled', 'approved') and days_remaining < 0:
            self.write({'state': 'expired'})

    @api.depends('date')
    def _compute_start_month(self):
        if self.date:
            self.start_month = self.date.month

    def process_month(self):
        quotations = self.env['service.quotation'].search([('date', '!=', False)])
        for quotation in quotations:
            quotation.start_month = quotation.date.month

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']
        st_number = SequenceObj.next_by_code('service.quotation')
        if vals.get('select_service') == 'qds':
            st_number = st_number.replace('QPS', 'QDS')
        vals['name'] = st_number
        res = super(ServiceQuotation, self).create(vals)
        return res

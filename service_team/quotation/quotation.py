# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
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
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    select_service = fields.Selection([('qps', 'Pest Control Service'), ('qds', 'Disinfection Service')],
                                      string="Choose Service", default='qps')
    product_id = fields.Many2one('product.product', string="Service Type")
    # job_area_id = fields.Many2one('job.area', string="Area Covered", required=False)
    service_description = fields.Char(string="Service Description")
    # job_type_id = fields.Many2one('job.type', string="Job Type")
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
        scope_of_works = []
        covered_pests = []
        contractors_obligations = []
        client_obligations = []
        for sc in self.scope_of_works:
            scope_of_works.append(sc.id)
        for cp in self.covered_pests:
            covered_pests.append(cp.id)
        for obl in self.contractors_obligations:
            contractors_obligations.append(obl.id)
        for cli in self.client_obligations:
            client_obligations.append(cli.id)

        contract_payment = self.env['service.payment.term'].search([], limit=1)
        product = self.env['product.product'].search([('type', '=', 'service')], limit=1)
        vals = {
            'partner_id': self.partner_id if self.partner_id.id else False,
            'contact_id': self.contact_id if self.contact_id.id else False,
            'date': self.date,
            'payment_term_id': self.payment_term_id if self.payment_term_id.id else False,
            'amount': self.amount,
            'currency_id': self.currency_id if self.currency_id.id else False,
            'frequency_id': self.frequency_id if self.frequency_id.id else False,
            'callback_id': self.callback_id if self.callback_id.id else False,
            'employee_id': self.employee_id if self.employee_id.id else False,
            'covered_area': self.covered_area,
            'product_id': product.id,
            'date_start': fields.Date.today(),
            'contract_payment': contract_payment.id,
            'date_end': fields.Date.today(),
            'scope_of_works': [[6, 0, scope_of_works]],
            'covered_pests': [[6, 0, covered_pests]],
            'contractors_obligations': [[6, 0, contractors_obligations]],
            'client_obligations': [[6, 0, client_obligations]],
        }

        contract_pool = self.env['service.contract']
        contract = contract_pool.create(vals)
        contract_id = contract.id

        return {
            "name": "Contract",
            "type": 'ir.actions.act_window',
            "view_type": 'form',
            "view_mode": 'form',
            'res_model': "service.contract",
            "res_id": contract_id,
            'target': 'new'
        }

    @api.model
    def _cron_check_expiry(self):
        contracts = self.search([('state', '!=', 'cancelled')])
        contracts.get_expiry()

    @api.model
    def _cron_check_followup(self):
        order_ids = self.env['service.quotation'].search([('state', '=', 'valid')])
        template_id = self.env.ref('service_quotation.service_quotation_followup_mail_inherit')
        today = datetime.now().date()
        emp_lst = []
        for each in order_ids:
            if each.next_execution_date:
                next_execution_date = each.next_execution_date
                date_after_seven_days = datetime.strptime(str(next_execution_date), "%Y-%m-%d") + relativedelta(days=7)
                date_after_7_days = date_after_seven_days.date()
                # if True:
                if today == date_after_7_days:
                    if each.employee_id.id not in emp_lst:
                        emp_lst.append(each.employee_id.id)

        for each in emp_lst:
            service_quotation_detail_list = []
            count = 1
            for order_id in order_ids.filtered(lambda l: l.employee_id.id == each):
                next_execution_date = order_id.next_execution_date
                if next_execution_date:
                    date_after_seven_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(days=7)
                    date_after_7_days = date_after_seven_days.date()

                    if today == date_after_7_days:
                        service_quotation_details = {
                            'serial': count,
                            'name': order_id.name,
                            'partner_id': order_id.partner_id.name, 'date': order_id.date,
                            'amount': order_id.amount}
                        count += 1
                        service_quotation_detail_list.append(service_quotation_details)
                        order_id.write({'next_execution_date': date_after_7_days})
            if emp_lst:
                emp_id = self.env['hr.employee'].browse(each)
                if emp_id.work_email:
                    template_id.email_to = emp_id.work_email
                if template_id:
                    template_id.with_context({'quotation_list': service_quotation_detail_list}).send_mail(order_id.id, force_send=True)

    def get_expiry(self):
        today = fields.Date.today()
        today = datetime.strptime(today, '%Y-%m-%d')
        end_date = self.date
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        validity = self.validity_id
        validity_days = validity.numbers
        if not validity_days:
            # raise Warning("NO Validity Days Set on This Validity Term!!!!!!!")
            pass

        end_date = end_date + relativedelta(days=validity_days)
        delta = end_date - today
        days_remaining = delta.days
        state = self.state
        if state not in ('cancelled', 'approved'):
            if days_remaining < 0:
                self.write({'state': 'expired'})

    @api.depends('date')
    def _get_start_month(self):
        if self.date:
            self.start_month = int(datetime.strptime(str(self.date), '%Y-%m-%d').month)

    def process_month(self):
        accounts = self.env['account.move'].search([])
        for i in accounts:
            if i.date:
                month = int(datetime.strptime(i.date, '%Y-%m-%d').month)
                sql = """UPDATE service_quotation SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']
        st_number = SequenceObj.next_by_code('service.quotation')
        if vals.get('select_service') == 'qds':
            st_number = st_number.replace('QPS', 'QDS')
        vals['name'] = st_number
        res = super(ServiceQuotation, self).create(vals)
        return res

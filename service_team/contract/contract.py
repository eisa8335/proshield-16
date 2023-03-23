# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _name = "service.contract"
    _description = 'Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    select_service = fields.Selection([('cps', 'Pest Control Service'), ('cds', 'Disinfection Service')], string="Choose Service", default='cps')
    paid_amount = fields.Float(string="Paid Amount", compute="_get_paid_amount", store=True)
    amount_balance = fields.Float(string="Amount Balance", compute="_get_amount_balance", store=True)
    next_job_date = fields.Datetime(string="Next Job On", compute="_get_next_job", store=True)
    job_count = fields.Integer(string="Jobs Count", compute="_get_job_count", store=True)
    invoice_count = fields.Integer(string="Invoice Count", compute="_get_invoice_count", store=True)
    state = fields.Selection([('draft', 'Draft'), ('valid', 'Valid'), ('expiring', 'Expiring'), ('expired', 'Expired'),
                              ('renewed', 'Renewed'), ('not_renewed', 'Not-Renewed'), ('cancelled', 'Cancelled')],
                             string="Status", default='draft')
    signed_copy = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Received Signed Copy", default='no')
    date_start = fields.Date(string="Contract Start Date", required=True)
    date_end = fields.Date(string="Contract End Date", required=True)
    name = fields.Char(string="Contract Reference", readonly=False)
    scope_of_works = fields.Many2many('service.scope.work', 'rel_contract_scope', 'quotation_id', 'scope_id',
                                      string="Scope Of Work", required=True)
    covered_pests = fields.Many2many('covered.pest', 'rel_contract_pest', 'quotation_id', 'pest_id', string="Covered Pest", required=True)
    contractors_obligations = fields.Many2many('contract.obligation', 'rel_contract_contra_oblig', 'contract_id', 'obligation_id', string="Contractor's Obligation", required=True)
    client_obligations = fields.Many2many('client.obligation', 'rel_contract_client_oblig', 'contract_id', 'clie_obliga_id', string="Client Obligation", required=True)
    product_id = fields.Many2one('product.product', string="Service", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    contact_id = fields.Many2one('res.partner', string="Contact")
    date = fields.Date(string="Contract Date", default=fields.Date.today)
    # job_area_id = fields.Many2one('job.area', string="Area Covered", required=False)
    service_description = fields.Char(string="Service Description")
    amount = fields.Float(string="Contract Value", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    contract_payment = fields.Many2one('service.payment.term', string="Contract Payment", required=True)
    payment_term_id = fields.Many2one('account.payment.term', string="Payment Term", required=True)
    frequency_id = fields.Many2one('service.frequency', string="Frequency Of Treatment", required=True)
    callback_id = fields.Many2one('service.callback', string="Callbacks", required=True)

    covered_area = fields.Text(string="Covered Areas", required=True)
    remarks = fields.Text(string="Remarks")
    employee_id = fields.Many2one('hr.employee', string="Signed By", required=True, default=_default_employee)

    recurring_job = fields.Boolean(string="Recurring Job", copy=False)
    job_recurring_days = fields.Selection([(str(x), str(x) + ' Days') for x in range(1, 8)], string="Recurring Job After", copy=False)
    job_duration = fields.Float(string="Job Duration", default=2.0)
    job_start_time = fields.Datetime(string="Job Start Time", required=True)
    account_manager_id = fields.Many2one('hr.employee', string="Account Manager")
    # team_id = fields.Many2one('service.team', string="Preferred Team")
    ref = fields.Text(string="Internal Ref")
    next_execution_date = fields.Date(string="Next Execution Date")
    start_month = fields.Integer(compute='_get_start_month', store=True)
    project_name = fields.Char(sting="Project Name")

    @api.constrains('date_start', 'date_end')
    def _check_date(self):
        date_start = self.date_start
        date_end = self.date_end
        if date_start > date_end:
            raise ValidationError("End Date Must Be Greater than Start Date!")

    def _get_job_count(self):
        contract_id = self.id
        obj_pool = self.env['calendar.event'].search([('contract_id', '=', contract_id)])
        self.job_count = len(obj_pool)

    def _get_invoice_count(self):
        contract_id = self.id
        obj_pool = self.env['account.invoice'].search([('contract_id', '=', contract_id)])
        self.invoice_count = len(obj_pool)

    def _get_journal(self):
        journal_pool = self.env['account.journal']
        journal_id = journal_pool.search([('type', '=', 'sale')], limit=1)
        if not journal_id:
            raise ValidationError("There is No Journal with type Sale ,Pls Configure One")
        return journal_id

    def get_number_of_days(self):
        date_start = self.date_start
        date_end = self.date_end
        date_start = datetime.strptime(date_start, '%Y-%m-%d')
        date_end = datetime.strptime(date_end, '%Y-%m-%d')
        delta = date_end - date_start
        return delta.days + 1

    def button_create_jobs(self):
        if self.job_count > 0:
            raise ValidationError("Already Jobs Are Created! if you Want Create New Ones, Please Delete All First")
        job_pool = self.env['calendar.event']
        job_type = self.env['job.type'].search([('name', '=', 'Contract')], limit=1)
        start_time = self.job_start_time
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        frequency_id = self.frequency_id
        freq = frequency_id.numbers
        total_days = self.get_number_of_days()
        freq_period_days = total_days / freq
        job_duration = self.job_duration
        job_value = self.amount / freq or 0.0
        recurring = self.recurring_job
        job_rec_days = self.job_recurring_days or False
        job_area_id = self.job_area_id and self.job_area_id.id or False,
        service_description = self.service_description
        if not freq:
            raise ValidationError("The Frequency Not set Number, Please Set it")
        contract_name = self.name or ''
        if not job_type:
            raise ValidationError("There is No Job Type Named Contract, Please Create One")
        for x in range(1, freq + 1):
            stop_time = start_time + relativedelta(hours=job_duration)
            stop_time = str(stop_time)
            vals = {
                'contract_id': self.id,
                'partner_id': self.partner_id if self.partner_id.id else False,
                'contact_id': self.contact_id if self.contact_id.id else False,
                'product_id': self.product_id if self.product_id.id else False,
                'job_type_id': job_type.id,
                'warranty': '0',
                'amount': 0.0,
                'state': 'Unconfirmed',
                'remarks': 'Job Number  ' + str(x) + '/ ' + str(freq) + ' of Contract : ' + contract_name,
                'start': str(start_time),
                'address': (self.partner_id.street or '') + '-' + (self.partner_id.street2 or ''),
                'stop': stop_time,
                'recurring_job': recurring,
                'job_recurring_days': job_rec_days,
                'job_value': job_value,
                'job_area_id': job_area_id,
                'service_description': service_description,
            }
            job = job_pool.create(vals)
            if recurring and job_rec_days:
                job.with_context({'from_contract': True, 'job_value': job_value, 'job_area_id': job_area_id, 'service_description': service_description}).create_recurring_job()
            start_time = start_time + relativedelta(days=freq_period_days)

    def button_create_invoice(self):
        if self.invoice_count > 0:
            raise ValidationError("Already Invoices Are Created! if you Want Create New Ones, Please Delete All First")
        invoice_pool = self.env['account.move']
        product_pool = self.env['product.product']
        journal_id = self._get_journal()
        contract_payment = self.contract_payment
        numbers = contract_payment.numbers
        if not numbers:
            raise ValidationError("Please Add Numbers in Contract Payment")
        date_freq = 12 / numbers
        date = self.job_start_time[:10]
        partner = self.partner_id
        total_amount = self.amount
        unit_amount = total_amount / numbers
        for x in range(1, numbers + 1):
            vals = {
                'name': self.name or '',
                'date_invoice': date,
                'journal_id': journal_id.id,
                'partner_id': partner.id,
                'account_id': partner.property_account_receivable_id.id if partner.property_account_receivable_id else False,
                'contract_id': self.id,
                'payment_term_id': self.payment_term_id if self.payment_term_id.id else False
            }
            invoice_line_val = {}
            name = 'Payment No-' + str(x) + ' Contract Ref: ' + self.name or ''
            credit_account_id = journal_id.default_credit_account_id.id if journal_id.default_credit_account_id else False
            contract_pdt_id = 129
            invoice_line_val['account_id'] = credit_account_id
            invoice_line_val['name'] = name
            invoice_line_val['product_id'] = contract_pdt_id
            invoice_line_val['quantity'] = 1
            invoice_line_val['price_unit'] = unit_amount

            product = product_pool.browse(contract_pdt_id)
            tax_ids = [tax.id for tax in product.taxes_id]
            invoice_line_val['invoice_line_tax_ids'] = [[6, False, tax_ids]]
            vals['invoice_line_ids'] = [(0, 0, invoice_line_val)]
            invoice = invoice_pool.create(vals)
            date = datetime.strptime(date, '%Y-%m-%d')
            date = date + relativedelta(months=date_freq)
            date = str(date)
            date = date[:10]

    @api.onchange('date_start')
    def onchange_date_star(self):
        date_start = self.date_start
        if date_start:
            date_start = datetime.strptime(str(date_start), '%Y-%m-%d')
            date_end = date_start + relativedelta(years=1, days=-1)
            self.date_end = str(date_end)

    def button_open_invoices(self):
        ctx = {
            'default_contract_id': self.id,
            'default_partner_id': self.partner_id.id if self.partner_id else False,
        }
        domain = [('contract_id', '=', self.id)]
        # Select the view
        tree_view = self.env.ref('account.invoice_tree', False)
        form_view = self.env.ref('account.invoice_form', False)

        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'context': ctx,
            'domain': domain,
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'type': 'ir.actions.act_window',
        }

    def button_open_jobs(self):
        ctx = {
            'default_contract_id': self.id,
            'default_partner_id': self.partner_id.id if self.partner_id else False,
        }
        domain = [('contract_id', '=', self.id)]
        # Select the view
        tree_view = self.env.ref('service_team.cal_scheduling_view_tree', raise_if_not_found=False)
        form_view = self.env.ref('service_team.view_cal_scheduling_form', raise_if_not_found=False)

        return {
            'name': _('Jobs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'calendar.event',
            'context': ctx,
            'domain': domain,
            'views': [(tree_view if tree_view.id else False, 'tree'), (form_view if form_view.id else False, 'form')],
            'type': 'ir.actions.act_window',
        }

    def button_confirm(self):
        for rec in self:
            rec.state = 'valid'

    def button_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def button_renewed(self):
        for rec in self:
            rec.state = 'renewed'

    def button_not_renewed(self):
        for rec in self:
            rec.state = 'not_renewed'

    def check_expiry(self):
        today = fields.Date.today()
        today = datetime.strptime(today, '%Y-%m-%d')
        end_date = self.date_end
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date - today
        days_remaining = delta.days

        if days_remaining < 0:
            return True
        return False

    def button_reinstate(self):
        already_expired = self.check_expiry()
        if already_expired:
            raise ValidationError("Its Already Expired!")
        self.write({'state': 'draft'})

    @api.model
    def _cron_check_expiry(self):
        contracts = self.search([('state', '!=', 'cancelled')])
        contracts.get_expiry()

    @api.model
    def _cron_check_followup(self):
        order_ids = self.env['service.contract'].search([('state', 'in', ['expired', 'expiring'])])
        template_id = self.env.ref('service_team.service_contract_followup_mail_inherit')
        today = datetime.now().date()
        emp_lst = []
        for each in order_ids:
            if each.next_execution_date:
                next_execution_date = each.next_execution_date
                date_after_fifteen_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(days=15)
                date_after_15_days = date_after_fifteen_days.date()
                if today == date_after_15_days:
                    if each.employee_id.id not in emp_lst:
                        emp_lst.append(each.employee_id.id)

        for each in emp_lst:
            service_contract_detail_list = []
            count = 1
            for order_id in order_ids.filtered(lambda l: l.employee_id.id == each):
                if order_id.next_execution_date:
                    next_execution_date = order_id.next_execution_date
                    date_after_fifteen_days = datetime.strptime(next_execution_date, "%Y-%m-%d") + relativedelta(
                        days=15)
                    date_after_15_days = date_after_fifteen_days.date()
                    if today == date_after_15_days:
                        service_contract_details = {
                            'serial': count,
                            'name': order_id.name,
                            'partner_id': order_id.partner_id.name,
                            'date_start': order_id.date_start,
                            'date_end': order_id.date_end,
                            'amount': order_id.amount,
                        }
                        count += 1
                        service_contract_detail_list.append(service_contract_details)
                        order_id.next_execution_date = date_after_15_days
            if emp_lst:
                emp_id = self.env['hr.employee'].browse(each)
                if emp_id.work_email:
                    template_id.email_to = emp_id.work_email
                if template_id:
                    template_id.with_context({'quotation_list': service_contract_detail_list}).send_mail(order_id.id, force_send=True)

    def get_expiry(self):
        today = fields.Date.today()
        today = datetime.strptime(today, '%Y-%m-%d')
        end_date = self.date_end
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date - today
        days_remaining = delta.days
        state = self.state
        if state not in ('cancelled', 'renewed', 'not_renewed'):
            if 30 >= days_remaining >= 0:
                self.write({'state': 'expiring'})
            if days_remaining < 0:
                self.write({'state': 'expired'})

    def _get_next_job(self):
        job_pool = self.env['calendar.event']
        job_ids = job_pool.search([('contract_id', '=', self.id)])
        res = []
        for job in job_ids:
            res.append((job.id, job.start))
        current_time = str(datetime.now())
        for job in res:
            if job[1] < current_time:
                res.remove(job)
        res.sort(key=lambda tup: tup[1])
        if res:
            self.next_job_date = res[0][1]

    def _get_amount_balance(self):
        invoice_pool = self.env['account.move']
        invoice_ids = invoice_pool.search([('contract_id', '=', self.id)])

        amount_balance = 0.0
        for invoice in invoice_ids:
            amount_balance += invoice.residual
        self.amount_balance = amount_balance

    @api.onchange('date_end')
    def onchange_date_end(self):
        if self.date_end:
            end_date = datetime.strptime(str(self.date_end), "%Y-%m-%d") - relativedelta(days=30)
            self.next_execution_date = end_date.date()

    def _get_paid_amount(self):
        invoice_pool = self.env['account.move']
        invoice_ids = invoice_pool.search([('contract_id', '=', self.id), ('state', 'in', ('open', 'paid'))])
        paid_amount = sum([inv.amount_total - inv.residual for inv in invoice_ids])
        self.paid_amount = paid_amount

    @api.depends('date_start')
    def _get_start_month(self):
        if self.date_start:
            self.start_month = int(datetime.strptime(str(self.date_start), '%Y-%m-%d').month)

    @api.model
    def process_month(self):
        accounts = self.env['service.contract'].search([])
        for i in accounts:
            if i.date:
                month = int(datetime.strptime(i.date_start, '%Y-%m-%d').month)
                sql = """UPDATE service_contract SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']
        st_number = SequenceObj.next_by_code('service.contract')
        if vals.get('select_service') == 'cds':
            st_number = st_number.replace('CPS', 'CDS')
        vals['name'] = st_number
        return super(Contract, self).create(vals)

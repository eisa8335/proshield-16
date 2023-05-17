# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date, datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class JobType(models.Model):
    _name = "job.type"
    _description = "Job Type"

    name = fields.Char(string="Job Type")


class Event(models.Model):
    _inherit = "calendar.event"
    _description = 'Job Event'
    _rec_name = "job_id"

    def get_warrant_selection(self):
        selection = [('0', 'No Warranty')]
        selection_ext = [(str(x), str(x) + ' Months') for x in range(1, 13)]
        selection.extend(selection_ext)
        return selection

    stop = fields.Datetime(string="Stop", compute="_get_stop_time", required=False, store=True)
    name = fields.Char(string="Job Description", default='/')
    job_area_id = fields.Many2one('job.area', string="Area Covered", required=False)
    service_description = fields.Char(string="Service Description")
    vat_included = fields.Boolean(string="VAT Included")
    vat_amount = fields.Float(string="VAT Amount", compute="_get_vat_amount", store=True)
    job_id = fields.Char(string="Job ID", readonly=True)
    display_start_date = fields.Char('Display Start Date', compute='_compute_display_start_time', store=True)
    display_start_time = fields.Char('Display Start Time', compute='_compute_display_start_time', store=True)
    contract_id = fields.Many2one('service.contract', string="Contract")
    parent_job_id = fields.Many2one('calendar.event', string="Parent Job")
    parent_job_card = fields.Integer(string="#Parent Job", compute='_get_parent_job_card', readonly=True, store=True)
    state = fields.Selection([('unconfirmed', 'Unconfirmed'), ('scheduled', 'Scheduled'), ('completed', 'Completed'),
                              ('cancelled', 'Cancelled'), ('received', 'Received'), ], string='Status', readonly=True,
                             copy=False, default='scheduled')
    contact_id = fields.Many2one('res.partner', string="Contact")
    contact_mobile = fields.Char(string="Contact Mobile", related='contact_id.mobile', store=True)
    block = fields.Boolean(string="Block")
    block_label = fields.Char(string="Block Label", compute='get_block_label', store=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    area_id = fields.Many2one('area.area', string="Area", related='partner_id.area_id', store=True, readonly=False)
    premise_type_id = fields.Many2one('premise.type', string="Premise Type", related='partner_id.premise_type_id',
                                      store=True, readonly=False)
    job_value = fields.Float(string="Average Job Value", readonly=True)
    call_back = fields.Boolean(string="Call Back")
    call_back_team_id = fields.Many2one('service.team', string="Call Back")
    phone = fields.Char(string="Phone", related='partner_id.phone', store=True, readonly=False)
    street = fields.Char(string="Address", related='partner_id.street', store=True, readonly=False)
    street2 = fields.Char(string="Address2", related='partner_id.street2', store=True, readonly=False)
    partner_latitude = fields.Float(string="Lat", digits=(16, 5), related='partner_id.partner_latitude', store=True,
                                    readonly=False)
    partner_longitude = fields.Float(string="Long", digits=(16, 5), related='partner_id.partner_longitude', store=True,
                                     readonly=False)
    warranty = fields.Selection(get_warrant_selection, string="Warranty")
    warranty_counter = fields.Char(string="Warranty Counter", compute="_get_remaining_days", store=True)
    completed_on = fields.Date(string="Completed On")
    product_id = fields.Many2one('product.product', string="Service Type")
    job_type_id = fields.Many2one('job.type', string="Job Type")
    mobile = fields.Char(string="Mobile", related='partner_id.mobile', store=True, readonly=False)
    service_team = fields.Many2one('service.team', string="Team")
    amount = fields.Float(string="Amount")
    remarks = fields.Text(string="Remarks", translate=True)
    followup_visit = fields.Boolean(string="Follow Up Visit")
    followup_days = fields.Selection([(str(x), str(x) + ' Days') for x in range(1, 31)], string="Follow Up After")
    invoice_date = fields.Date(string="Invoice Date")
    job_date = fields.Date(string="Job Date", readonly=True)
    recurring_job = fields.Boolean(string="Recurring Job", copy=False)
    job_recurring_days = fields.Selection([(str(x), str(x) + ' Days') for x in range(1, 8)],
                                          string="Recurring Job After", copy=False)
    recurring_job_created = fields.Boolean(string="Recurring Job Created")
    job_card = fields.Char(string="Job Card#", size=5, copy=False)
    jcn_not_required = fields.Boolean(string="JCN Not Required")
    job_duration = fields.Float(string="Job Duration", compute='_get_job_duration', store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", )
    paid_amount = fields.Float(string="Paid Amount", readonly=True, compute="_get_inv_amount", store=True)
    balance = fields.Float(string="Balance", readonly=True, compute="_get_inv_amount", store=True)
    invoice_amount = fields.Float(string="Invoice Amount", compute="_get_inv_amount", store=True)
    invoice_tax = fields.Float(string="Tax Amount", compute="_get_inv_amount", store=True)
    internal_note = fields.Text(string="Internal Note")
    _sql_constraints = [
        ('job_card_uniq', 'unique(job_card)', 'Job Card Number must be unique!'),
    ]
    start_month = fields.Integer(compute='_get_start_month', store=True)

    def _get_display_start_time(self, start, stop, zduration, zallday):
        """ Return date and time (from to from) based on duration with timezone in string. Eg :
                1) if user adds a duration of 2 hours, return: August-23-2013 at (04-30 To 06-30) (Europe/Brussels)
                2) if the event is all day, return: AllDay, July-31-2013
        """
        timezone = self.env.context.get('tz') or self.env.user.partner_id.tz or 'UTC'

        # Get date/time format according to context
        format_date, format_time = self.with_context(tz=timezone)._get_date_formats()

        # Convert date and time into user timezone
        date = fields.Datetime.context_timestamp(self.with_context(tz=timezone), fields.Datetime.from_string(start))
        date_deadline = fields.Datetime.context_timestamp(self.with_context(tz=timezone),
                                                          fields.Datetime.from_string(stop))

        # Convert date and time to string using user formats
        date_str = fields.Date.to_string(date.date())
        time_str = fields.Datetime.to_string(date.time())

        display_date = _(date_str)
        display_start_time = _(time_str)

        return display_date, display_start_time

    def _compute_display_start_time(self):
        for meeting in self:
            meeting.display_start_date, meeting.display_start_time = self._get_display_start_time(meeting.start,
                                                                                                  meeting.stop,
                                                                                                  meeting.duration,
                                                                                                  meeting.allday)

    @api.depends('block')
    def get_block_label(self):
        for rec in self:
            rec.block_label = ''
            if rec.block:
                rec.block_label = "#Block"

    def _get_remaining_days(self):
        for rec in self:
            completd_on = rec.completed_on
            if completd_on:
                warranty = int(rec.warranty)
                if warranty:
                    today = datetime.now()
                    warranty_date = completd_on + relativedelta(months=warranty, days=1)
                    remaining_days = str(warranty_date - today)
                    remaining_days = remaining_days.split(',')
                    rec.warranty_counter = remaining_days[0]

    @api.depends('start', 'job_duration')
    def _get_stop_time(self):
        for record in self:
            start = record.start
            if start:
                job_duration = record.job_duration or 2.0
                stop = start + relativedelta(hours=job_duration)
                record.stop = stop

    def _get_parent_job_card(self):
        if self.parent_job_id:
            self.parent_job_card = self.parent_job_id.job_card

    def _get_duration_from_job(self):
        self.duration = self.job_duration or 2.0

    @api.depends('vat_included', 'amount', 'product_id')
    def _get_vat_amount(self):
        for rec in self:
            if not rec.vat_included and rec.amount:
                rec.vat_amount = rec.amount * (5 / 100)

    @api.depends('start')
    def _get_start_month(self):
        for rec in self:
            if rec.start:
                rec.start_month = rec.start.month

    def process_month(self):
        jobs = self.env['calendar.event'].search([])
        for i in jobs:
            if i.start:
                month = i.start.month
                sql = """UPDATE calendar_event SET start_month = %s WHERE id = %s""" % (month, i.id)
                self.env.cr.execute(sql)

    @api.constrains('state', 'service_team')
    def _get_state_constrain(self):
        if self.state == 'unconfirmed' and self.service_team.id:
            raise ValidationError("You Cannot Assign A Service Team In Unconfirmed State")

    @api.onchange('followup_visit', 'recurring_job')
    def onchage_followup(self):
        if self.followup_visit:
            self.recurring_job = False
        if self.recurring_job:
            self.followup_visit = False

    @api.depends('invoice_id')
    def _get_inv_amount(self):
        invoice_id = self.invoice_id
        if invoice_id:
            invoice_total = invoice_id.amount_total
            balance = invoice_id.amount_residual
            paid_amount = invoice_total - balance
            self.invoice_amount = invoice_total
            self.paid_amount = paid_amount
            self.balance = balance
            self.invoice_tax = invoice_id.amount_tax

    @api.depends('start', 'stop')
    def _get_job_duration(self):
        for rec in self:
            if rec.start and rec.stop:
                duration = (rec.stop - rec.start).total_seconds() / 3600
                rec.job_duration = duration
            else:
                rec.job_duration = 0

    def get_inv_balance(self):
        balance = 0.0
        invoice_id = self.invoice_id
        if invoice_id:
            balance = invoice_id.amount_residual
        return balance

    def get_inv_amount(self):
        self._get_inv_amount()

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']
        st_number = SequenceObj.next_by_code('job.event')
        vals['job_id'] = st_number
        vals['name'] = st_number
        if not vals.get('invoice_date', False):
            if isinstance(vals.get('start'), str):
                vals['invoice_date'] = datetime.strptime(vals.get('start'), "%Y-%m-%d %H:%M:%S").date()
            else:
                vals['invoice_date'] = vals.get('start').date()
        if vals.get('start', False):
            if isinstance(vals.get('start'), str):
                vals['job_date'] = datetime.strptime(vals.get('start'), "%Y-%m-%d %H:%M:%S").date()
            else:
                vals['job_date'] = vals.get('start').date()
        res = super(Event, self).create(vals)
        if res.partner_id.company_type == 'person' and res.state != 'unconfirmed':
            res.send_smsnow()
        return res

    def write(self, vals):
        rec = super(Event, self).write(vals)
        if vals.get('start') or vals.get('stop'):
            for res in self:
                if isinstance(vals.get('start'), str):
                    res.invoice_date = datetime.strptime(vals.get('start'), "%Y-%m-%d %H:%M:%S").date()
                else:
                    res.invoice_date = vals.get('start').date()
                if vals.get('job_type_id'):
                    job = self.env['job.type'].browse(vals.get('job_type_id'))
                else:
                    job = res.job_type_id
                if job.name == 'One Time Job' and res.partner_id.company_type == 'person' and res.state != 'cancelled':
                    res.send_smsnow(mssg="has been successfully rescheduled")
        return rec

    def assign_parent_balance(self):
        balance = 0.0
        parent_job_id = self.parent_job_id
        if parent_job_id:
            balance = parent_job_id.get_inv_balance()
        return balance

    @api.model
    def _cron_check_followup(self):
        today = fields.Date.today()
        job_ids = self.env['calendar.event'].search(
            [('job_type_id.name', '=', 'One Time Job'), ('state', '=', 'received')])
        for each in job_ids:
            if each.partner_id.company_type == 'person':
                next_execution_date = each.start
                date_after_seven_days = next_execution_date + relativedelta(months=6, days=7)
                date_after_7_days = date_after_seven_days
                if today == date_after_7_days:
                    sms_pool = self.env['sms.sms']
                    default_str = "It's time to protect again from the unwanted pests. 'Pest Free & Stress Free' For Bookings please call 043888235. Thank you <br/> Pro Shield Pest Control Services"
                    mob_no = each.partner_id.mobile
                    if not mob_no:
                        raise ValidationError("NO Mobile Number")
                    #         mob_no = '+971508887556'

                    vals = {
                        'number': mob_no,
                        'body': default_str
                    }
                    sms = sms_pool.create(vals)
                    sms.send()

    def send_smsnow(self, mssg='is confirmed'):
        signature = self.env['res.users'].sudo().browse(self._uid).signature
        format_date = "%a %b %d"
        format_time = "%H:%M:%S"
        sms_pool = self.env['sms.sms']
        #         config_id = self.env['sms.mail.server'].browse(1)
        sam = datetime.strptime(str(self.start), DEFAULT_SERVER_DATETIME_FORMAT)
        sam = sam + timedelta(hours=4)
        now = datetime.now()
        """Intentional"""
        # if now > sam:
        #     raise ValidationError("Past Job....NOT Sending SMS")
        formated_date = sam.strftime(format_date)
        formated_time = sam.strftime(format_time)
        default_str = 'Dear %s <br/> Your appointment %s on %s at %s. For any queries call 043888235. <br/> Thank you <br/> Pro Shield Pest Control Services L.L.C' % (
            self.partner_id.name, mssg, formated_date, formated_time)
        mob_no = self.partner_id.mobile
        # if not mob_no:
        #     raise ValidationError("NO Mobile Number")

        vals = {
            'number': mob_no,
            'body': default_str
        }
        sms = sms_pool.create(vals)
        sms.send()

    def reinstate(self):
        self.write({'state': 'scheduled'})

    def confirm(self):
        balance = self.assign_parent_balance()
        self.write({'state': 'scheduled', 'amount': balance})

    def unconfirm(self):
        self.write({'state': 'unconfirmed'})

    def complete(self):
        if not self.service_team:
            raise ValidationError("Please Choose the Team Please......")
        today = date.today()

        self.write({'state': 'completed', 'completed_on': today})

    def cancel(self):
        self.write({'state': 'cancelled'})

    def receive(self):
        self.get_inv_amount()
        self.create_followup()
        if self.partner_id.company_type == 'person' and self.paid_amount > 0.0:
            sms_pool = self.env['sms.sms']
            default_str = 'Dear %s <br/> Your payment of %s AED is received & registered in our system. Thank you for choosing Pro Shield Pest Control Services. For any query plz call <br/> 043888235' % (
                self.partner_id.name, self.paid_amount)
            mob_no = self.partner_id.mobile
            if not mob_no:
                raise ValidationError("NO Mobile Number")
            #         mob_no = '+971508887556'

            vals = {
                'number': mob_no,
                'body': default_str
            }
            sms = sms_pool.create(vals)
            sms.send()
        self.write({'state': 'received'})

    @api.onchange('area_id')
    def onchange_area_id(self):
        if self.area_id:
            self.location = self.area_id.name if self.area_id else ''

    @api.onchange('product_id')
    def onchange_product_id(self):
        product_id = self.product_id
        if product_id:
            self.amount = product_id.lst_price

    def create_followup(self):
        if self.followup_visit and int(self.followup_days):
            followup_days = int(self.followup_days)
            start = self.start + timedelta(days=followup_days)
            stop = self.stop + timedelta(days=followup_days)
            self._get_inv_amount()
            remark = (self.remarks or '') + ' Follow Up for Job Id ' + str(self.job_id) + ' Done By ' + (
                    self.service_team.name or '') + ' On ' + (self.display_start_date or '') + ' ' + (
                             self.display_start_time or '')
            job_type = self.env['job.type'].search([('name', '=', 'Follow Up')], limit=1)
            job_type_id = job_type.id if job_type else self.env['job.type'].search(
                [('name', '=', 'Second Visit')]).id or False
            default = {
                'service_team': False,
                'start': start,
                'stop': stop,
                'amount': self.balance,
                'job_card': False,
                'parent_job_id': self.id,
                'remarks': remark,
                'job_type_id': job_type_id,
                'followup_visit': False,
                'followup_days': False,
                'state': 'unconfirmed'
            }
            self.copy(default)

    def create_recurring_job(self):
        state = 'scheduled'
        job_area_id = False
        service_description = ''
        job_value = 0.0
        context = self.env.context
        if context.get('from_contract', False):
            state = 'unconfirmed'
        if context.get('job_value', False):
            job_value = context.get('job_value', 0.0)
        if context.get('job_area_id', False):
            job_area_id = context.get('job_area_id', False)
        if context.get('service_description', ''):
            service_description = context.get('service_description', '')
        if self.recurring_job and self.job_recurring_days:
            start = self.start
            stop = self.stop
            if not stop:
                job_duration = self.job_duration or 2.0
                stop = start + relativedelta(hours=job_duration)
            adding_days = 1
            recurring_days = int(self.job_recurring_days)
            parent_job_id = self.id
            remark = (self.remarks or '') + ' Recurring for Job Id ' + self.job_id
            for x in range(1, recurring_days + 1):
                start = start + relativedelta(days=int(adding_days))
                stop = stop + relativedelta(days=int(adding_days))

                default = {'service_team': False, 'start': start, 'stop': stop,
                           'amount': 0, 'job_card': False, 'parent_job_id': parent_job_id,
                           'remarks': remark,
                           'recurring_job': False,
                           'job_recurring_days': False,
                           'state': state,
                           'job_value': job_value,
                           'job_area_id': job_area_id,
                           'service_description': service_description
                           }
                self.copy(default)
        self.recurring_job_created = True

    def _get_journal(self):
        journal_pool = self.env['account.journal']
        journal_id = journal_pool.search([('type', '=', 'sale')], limit=1)
        if not journal_id:
            raise ValidationError("There is No Journal with type Sale ,Pls Configure One")
        return journal_id

    def get_product_account(self, product):
        return (product.property_account_income_id and product.property_account_income_id.id) or (
                product.categ_id and product.categ_id.property_account_income_categ_id and product.categ_id.property_account_income_categ_id.id)

    def create_invoice(self):
        if not self.amount:
            raise ValidationError("You can't invoice with 0.0 amount")
        if self.invoice_id:
            raise ValidationError("Already invoice attached")

        self.assign_parent_balance()
        invoice_pool = self.env['account.move']
        journal_id = self._get_journal()
        partner = self.partner_id

        vals = {
            'name': self.job_card,
            'invoice_date': self.invoice_date,
            'journal_id': journal_id.id,
            'partner_id': partner.id,
            'job_id': self.id,
            'job_card': self.job_card,
            'job_date': self.job_date,
            'job_type_id': self.job_type_id.id if self.job_type_id else False,
            'service_team_id': self.service_team.id if self.service_team else False,
        }

        invoice_line_vals = {}

        if self.product_id:
            product = self.product_id
            credit_account_id = self.get_product_account(product)
            name = product.description_sale or product.name or ''

            invoice_line_vals['product_id'] = product.id
            tax_ids = [tax.id for tax in product.taxes_id]
            invoice_line_vals['tax_ids'] = [(6, 0, tax_ids)]
            invoice_line_vals['account_id'] = credit_account_id
            invoice_line_vals['price_unit'] = self.amount
            invoice_line_vals['name'] = name
        else:
            name = 'No Product/Description'
            credit_account_id = journal_id.default_credit_account_id.id if journal_id.default_credit_account_id else False

            invoice_line_vals['account_id'] = credit_account_id
            invoice_line_vals['name'] = name
            invoice_line_vals['quantity'] = 1
            invoice_line_vals['price_unit'] = self.amount

        vals['invoice_line_ids'] = [(0, 0, invoice_line_vals)]
        invoice = invoice_pool.create(vals)

        invoice.action_post()
        self.invoice_id = invoice.id

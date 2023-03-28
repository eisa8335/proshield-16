# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo import tools, _


class ServiceTeam(models.Model):
    _name = "service.team"
    _description = 'Service Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    name = fields.Char('Service Team', required=True, translate=True)
    user_id = fields.Many2one('hr.employee', string='Team Leader')
    driver_id = fields.Many2one('hr.employee', string='Team Driver')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    team_vehicle = fields.Many2one('fleet.vehicle', string="Team Vehicle")
    active = fields.Boolean(default=True,
                            help="If the active field is set to false, it will allow you to hide the sales team without removing it.")
    member_ids = fields.Many2many('hr.employee', 'service_team_rel', 'service_team_id', 'employee_id',
                                  string='Team Members')
    color = fields.Integer(string='Color Index', help="The color of the team")
    collection_record_id = fields.One2many('collect.record', 'record_id')

    def open_jobs(self):
        team_id = self.id
        domain = [('service_team', '=', team_id)]
        context = {'default_service_team': team_id}
        return {
            'name': _('Jobs'),
            'domain': domain,
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'calendar.event',
            'type': 'ir.actions.act_window',
        }

    def collect_cash_team(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'service.team.collection',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_name': self.id},
            'target': 'new',
        }


class Area(models.Model):
    _name = "area.area"
    name = fields.Char(string="Area")


class CollectRecord(models.Model):
    _name = "collect.record"

    record_id = fields.Many2one('service.team')
    date = fields.Date(readonly=True)
    name = fields.Many2one('service.team', string='Service Team', readonly=True)
    amount = fields.Float(string='Collected Amount', readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', readonly=True, default=lambda self: self.env.user)


class ServiceTeamCollection(models.TransientModel):
    _name = "service.team.collection"

    name = fields.Many2one('service.team', string='Service Team', readonly=True)
    cash_receivable = fields.Float(compute='_cash_on_hand', string='Receivable Amount', store=True)
    cash_on_hand = fields.Float(compute='_cash_on_hand', string='Cash On Hand', store=True)
    collect_cash = fields.Float('Collect Cash', required=True)

    def submit_amount(self):
        lis = []
        rec_id = self.env.context and self.env.context.get('active_ids', [])
        service_id = self.env['service.team'].browse(rec_id)
        vals = {
            'name': self.name.id,
            'date': fields.date.today(),
            'amount': self.collect_cash,
        }
        record = self.env['collect.record'].create(vals)
        lis.append(record.id)
        service_id.collection_record_id = lis

    @api.depends('name')
    def _cash_on_hand(self):
        for res in self:
            if res.name:
                invoice_obj = self.env['account.invoice']
                invoice_ids = invoice_obj.search(
                    [('service_team_id', '=', res.name.id), ('payment_state', 'in', ['not_paid', 'paid'])])
                if invoice_ids:
                    if res.name.collection_record_id:
                        total_amount = 0.0
                        for r in res.name.collection_record_id:
                            total_amount += r.amount
                        for line in invoice_ids:
                            res.cash_on_hand += line.amount_total - line.residual
                            res.cash_receivable += line.amount_total
                        res.cash_on_hand = res.cash_on_hand - total_amount
                        res.cash_receivable = res.cash_receivable - total_amount

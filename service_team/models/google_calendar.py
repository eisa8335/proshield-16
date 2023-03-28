# -*- coding: utf-8 -*-

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class GoogleCalendar(models.AbstractModel):
    STR_SERVICE = 'calendar'
    _inherit = 'google.%s' % STR_SERVICE

    def generate_data(self, event, isCreating=False):
        data = super(GoogleCalendar, self).generate_data(event, isCreating)
        summary = event.start[10:] + '-' + event.stop[10:]
        summary += '-' + event.name or ''
        if event.location:
            summary += '-' + event.location or ''
        description = ''
        if event.job_id:
            description = 'Job ID :' + event.job_id or ''
        if event.state:
            description += '\n' + 'Job Status :' + event.state or ''
        if event.start:
            description += '\n' + 'Time :' + event.start[10:] or ''
        if event.partner_id:
            description += '\n' + 'Customer Name :' + event.partner_id.name or ''
        if event.mobile:
            description += '\n' + 'Mobile :' + event.mobile or ''
        if event.amount:
            description += '\n' + 'Amount :' + str(event.amount) or ''
        if event.product_id:
            description += '\n' + 'Service Type :' + event.product_id.name or ''
        if event.job_type:
            description += '\n' + 'Job Type :' + event.job_type or ''

        description += '\n' + 'Follow Up :' + str(event.followup_visit) or ''

        description += '\n' + 'Geolocation'
        description += '\n' + 'Lat :' + str(event.partner_latitude) or ''
        description += '\n' + 'Long :' + str(event.partner_longitude) or ''
        if event.remarks:
            description += '\n' + 'Remarks :' + event.remarks or ''
        data.update({'summary': summary, 'description': description})
        return data

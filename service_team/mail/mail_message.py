# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models, SUPERUSER_ID, tools

_logger = logging.getLogger(__name__)


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'

    @api.model
    def create(self, values):

        #         message = super(Message, self).create(values)
        #
        #         message._notify(force_send=self.env.context.get('mail_notify_force_send', True),user_signature=self.env.context.get('mail_notify_user_signature', True))
        contract_channel_id = self.env.ref('service_team.channel_contract').id
        quotation_channel_id = self.env.ref('service_team.channel_quotation').id
        job_channel_id = self.env.ref('service_team.channel_job').id
        channel_ids = []
        if values.get('model') == 'service.contract':
            channel_ids.append(contract_channel_id)
        elif values.get('model') == 'service.quotation':
            channel_ids.append(quotation_channel_id)
        elif values.get('model') == 'calendar.event':
            channel_ids.append(job_channel_id)
        if channel_ids:
            values['channel_ids'] = [[6, False, channel_ids]]
        return super(Message, self).create(values)

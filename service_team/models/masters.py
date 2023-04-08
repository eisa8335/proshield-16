# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PremiseType(models.Model):
    _name = "premise.type"

    name = fields.Char(string="Premise Type")


class PremiseCategory(models.Model):
    _name = "premise.category"

    name = fields.Char(string="Premise Category")


class ClientSource(models.Model):
    _name = "client.source"

    name = fields.Char(string="Source")


class JobArea(models.Model):
    _name = "job.area"

    name = fields.Char(string="Area Covered")

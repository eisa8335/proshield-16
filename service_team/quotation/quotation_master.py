# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PaymentTerm(models.Model):
    _name = "service.payment.term"

    name = fields.Char(string="Payment Term")
    numbers = fields.Integer(string="Numbers")


class ServiceValidity(models.Model):
    _name = "service.validity"

    name = fields.Char(string="Payment Term")
    numbers = fields.Integer(string="Numbers")


class Frequency(models.Model):
    _name = "service.frequency"

    name = fields.Char(string="Frequency Of Treatment")
    numbers = fields.Integer(string="Numbers")


class WorkScope(models.Model):
    _name = "service.scope.work"
    name = fields.Char(string="Scope Of Work")


class CoveredPest(models.Model):
    _name = "covered.pest"

    name = fields.Char(string="Covered Pest")


class ServiceCallback(models.Model):
    _name = "service.callback"

    name = fields.Char(string="Callbacks")


class ContractObligation(models.Model):
    _name = "contract.obligation"

    name = fields.Char(string="Contractor's Obligation")


class ClientObligation(models.Model):
    _name = "client.obligation"

    name = fields.Char(string="Client Obligation")

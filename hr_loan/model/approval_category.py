# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ApprovalCategory(models.Model):
    _inherit = "approval.category"
    
    approval_type = fields.Selection(selection_add=[('loan', 'Create Loan')])

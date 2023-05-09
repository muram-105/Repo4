# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_count = fields.Integer(compute="_get_loan_counts", string='Loans')

    def _get_loan_counts(self):
        loan = self.env['approval.request']
        self.loan_count = loan.search_count([('employee_id', '=', self.id)])

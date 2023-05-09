# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line')

    @api.onchange('input_type_id')
    def on_change_input_type_id(self):
        if self.loan_line_id:
            self.name = str(self.loan_line_id.loan_id.name)

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrLoanType(models.Model):
    _name = "hr.loan.type"
    _description = "Loan Type"

    name = fields.Char(required=True)
    months = fields.Integer('Number of Months',
                            help='Default number of months to deduct the loan total amount for this type')
    one_time_loan = fields.Boolean('One Time Loan',
                                   help=" If checked, the employee will not be able to apply for this loan type again (it's used in some countries for marriage loans, pilgrimage...etc).")
    interest_rate = fields.Float(digits='Payroll')


class HrLoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "Loan Line"
    _order = 'discount_date'

    loan_id = fields.Many2one('approval.request', 'Loan Request', required=True, ondelete='cascade')
    discount_date = fields.Date('Settlement Date', required=True,
                                help='Date of which the settlement will apprear in payslip')
    amount = fields.Float(required=True, help='Amount of each payment', digits='Payroll')
    is_settled = fields.Boolean('Settled', readonly=True)
    remaining_amount = fields.Float(readonly=True, digits='Payroll')

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            vals['remaining_amount'] = vals['amount'] if 'amount' in vals else 0
        return super(HrLoanLine, self).create(vals_list)

    def write(self, vals):
        if 'amount' in vals:
            vals['remaining_amount'] = vals['amount']
        return super(HrLoanLine, self).write(vals)

    def unlink(self):
        for l in self:
            if l.is_settled:
                raise UserError(_('You cannot delete line already settled!'))

        return super(HrLoanLine, self).unlink()

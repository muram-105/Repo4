# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    input_line_ids = fields.One2many(copy=True)

    def get_all_inputs_total_amount(self, code):
        result = sum(self.input_line_ids.filtered(lambda x: x.input_type_id.code == code).mapped("amount"))
        return result

    @api.onchange('employee_id', 'date_from', 'date_to')
    def get_inputs(self):
        loan_line_obj = self.env['hr.loan.line']
        loan_input_type = self.env.ref('hr_loan.loan_other_input')
        self.input_line_ids = self.input_line_ids.filtered(lambda x: x.input_type_id != loan_input_type)
        res = []
        if self.employee_id and self.date_from and self.date_to:
            loan_obj_lines = loan_line_obj.search([('loan_id.employee_id', '=', self.employee_id.id)
                                                      , ('is_settled', '=', False)
                                                      , ('discount_date', '<=', self.date_to)
                                                      , ('loan_id.request_status', '=', 'approved')])
            loan_total = 0.0
            contract = self.contract_id
            for line in loan_obj_lines:
                loan_inputs = self.input_line_ids.filtered(
                    lambda x: line == x.loan_line_id or (x.input_type_id == loan_input_type and not x.loan_line_id))
                if loan_inputs:
                    loan_inputs.write({'amount': line.remaining_amount, 'loan_line_id': line.id})
                else:
                    self.input_line_ids = [(0, 0, {'input_type_id': loan_input_type.id,
                                                   'name': str(line.loan_id.name),
                                                   'code': 'LOAN', 'amount': line.remaining_amount,
                                                   'contract_id': contract.id, 'loan_line_id': line.id})]

    def refund_sheet(self):
        res = super(HrPayslip, self).refund_sheet()
        for rec in self:
            loan_inputs = rec.input_line_ids.filtered(lambda x: x.loan_line_id)
            if loan_inputs:
                loan_inputs.mapped('loan_line_id').write({'is_settled': False})
                for input in loan_inputs:
                    input.loan_line_id.remaining_amount = input.amount
        return res

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        vals = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
        loan_account_id = self.env.user.company_id.loan_account_id.id
        ref = self.env.user.company_id.reference_employee_in_journal_entries
        if loan_account_id == account_id and ref:
            vals["partner_id"] = (self.employee_id.user_id and self.employee_id.user_id.partner_id.id) or \
                                 (self.employee_id.address_home_id.id)

        return vals

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            for l in payslip.input_line_ids.filtered(lambda x: x.loan_line_id):
                loan_line = l.loan_line_id
                if loan_line.discount_date <= payslip.date_to:
                    loan_line.is_settled = not payslip.credit_note
                    loan_line.remaining_amount = 0.0 if not payslip.credit_note else l.amount
                else:
                    raise UserError(_('Loan %s not in period!') % (loan_line.loan_id.name))
        return res

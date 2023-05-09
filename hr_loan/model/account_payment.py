# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    loan_id = fields.Many2one('approval.request', 'Loan', help='Loan Record')

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        vals = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)
        if self.loan_id:
            for val in vals:
                val["name"] = False
        return vals

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'loan_id')
    def _compute_destination_account_id(self):
        res = super(AccountPayment, self.filtered(lambda x: not x.loan_id))._compute_destination_account_id()
        for pay in self.filtered(lambda y: y.loan_id):
            if not pay.loan_id.company_id.loan_account_id:
                raise UserError(_('Please set loan account for company!'))
            pay.destination_account_id = pay.loan_id.company_id.loan_account_id.id
        return res

    def action_post(self):
        """on payment post Update loan linked with this payment """

        for rec in self.filtered(lambda x: x.loan_id and x.payment_type == 'inbound'):
            company = self.env.user.company_id
            amount = rec.currency_id._convert(rec.amount, company.currency_id, company, fields.date.today())
            for line in rec.loan_id.loan_line_ids:
                if not line.is_settled and line.remaining_amount == amount:
                    line.is_settled = True
                    line.remaining_amount = 0.0
                    break
                elif not line.is_settled and line.remaining_amount > amount:
                    if line.remaining_amount - amount < 0.01:
                        line.is_settled = True
                    line.remaining_amount -= amount
                    break
                elif not line.is_settled and line.remaining_amount < amount:
                    amount -= line.remaining_amount
                    line.remaining_amount = 0.0
                    line.is_settled = True
        return super(AccountPayment, self).action_post()

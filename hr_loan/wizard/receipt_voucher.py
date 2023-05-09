# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.tests.common import Form
from odoo.exceptions import UserError


class ReceiptVoucher(models.TransientModel):
    _name = 'receipt.voucher'
    _description = "Receipt Voucher"

    amount = fields.Float(required=True)
    date = fields.Date(required=True)
    note = fields.Char(required=True)

    def create_payment(self):
        loan_id = self.env['approval.request'].browse(self._context.get('active_id', False))
        payment_method = self.env['account.payment.method'].browse(1)
        payment_form = Form(self.env['account.payment'].with_context({'default_payment_type': 'inbound',
                                                                      'default_partner_type': 'customer',
                                                                      'default_move_journal_types': ('bank', 'cash')}))

        payment_form.payment_type = "inbound"
        payment_form.date = self.date
        payment_form.ref = self.note
        payment_form.partner_type = 'customer'
        payment_form.amount = self.amount
        payment_form.loan_id = loan_id
        payment_form.payment_method_id = payment_method
        payment = payment_form.save()

        if loan_id.company_id.reference_employee_in_journal_entries and not loan_id.employee_id.address_home_id:
            raise UserError(
                _("Please make sure a user is linked to the employee and that the private address is filled."))
        elif loan_id.company_id.reference_employee_in_journal_entries:
            payment.partner_id = loan_id.employee_id.address_home_id

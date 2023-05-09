# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    reference_employee_in_journal_entries = fields.Boolean(string="Reference Employee In Journal Entries",
                                                           related='company_id.reference_employee_in_journal_entries',
                                                           readonly=False)
    loan_account_id = fields.Many2one('account.account', 'Loan Account', related='company_id.loan_account_id',
                                      readonly=False)

    payment_journal = fields.Many2one('account.journal', string='Default Payment Journal', related='company_id.payment_journal',
                                              readonly=False)

class Company(models.Model):
    _inherit = 'res.company'

    loan_account_id = fields.Many2one('account.account', 'Loan Account')
    reference_employee_in_journal_entries = fields.Boolean(string="Reference Employee In Journal Entries", default=True)
    payment_journal = fields.Many2one('account.journal', 'Default Payment Journal')

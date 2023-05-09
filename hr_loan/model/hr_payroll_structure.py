# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    @api.model
    def _get_default_rule_ids(self):
        res = super(HrPayrollStructure, self)._get_default_rule_ids()
        res += [(0, 0, {
            'name': 'Loans Rule',
            'sequence': 150,
            'code': 'LOR',
            'category_id': self.env.ref('hr_payroll.DED').id,
            'condition_select': 'python',
            'condition_python': """
result =  payslip.dict.get_all_inputs_total_amount('LOAN')""",
            'amount_select': 'code',
            'amount_python_compute': """
tot = 0
result =  -1 * payslip.dict.get_all_inputs_total_amount('LOAN')""",
        }), ]

        return res

    rule_ids = fields.One2many(default=_get_default_rule_ids)

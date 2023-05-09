# -*- coding: utf-8 -*-
{
    'name': 'SW - Employee Loans Management',
    'summary': "One significant module to manage all your employees loans",
    'author': 'Smart Way Business Solutions',
    'website': 'https://www.smartway.co',
    'category': 'Human Resources',
    'version': '1.1',
    'depends': ['web', 'approvals', 'hr', 'hr_contract', 'hr_payroll_account'],
    'license': "Other proprietary",
    'data': [
        "security/rules.xml",
        "security/ir.model.access.csv",
        "data/approval_category_data.xml",
        "data/hr_payslip_input_type_data.xml",
        "wizard/receipt_voucher_view.xml",
        "views/account_payment_views.xml",
        "views/approval_request_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_payslip.xml",
        "views/loan_type_views.xml",
        "views/res_config_settings_views.xml"
    ]
}

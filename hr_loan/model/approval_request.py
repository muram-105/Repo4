# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tests.common import Form


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    contract_id = fields.Many2one('hr.contract', string='Current Contract',
                                  domain="[('company_id', '=', company_id)]", help='Current contract of the employee')


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    contract_id = fields.Many2one(groups="base.group_user")


class ApprovalRequest(models.Model):

    _inherit = "approval.request"

    @api.model
    def default_get(self, fields):
        defaults = super(ApprovalRequest, self).default_get(fields)
        if defaults.get('category_id', False) and self.env['approval.category'].browse(defaults.get('category_id', False)).approval_type == 'loan':
            defaults["employee_id"] = self.env.user.employee_id
            if not defaults.get('name', False):
                categ = self.env["approval.category"].browse(defaults.get('category_id', False))
                defaults['name'] = categ.sequence_id.next_by_id()
        return defaults

    employee_id = fields.Many2one('hr.employee', 'Employee', help='Employee Name', tracking=True, )
    type_id = fields.Many2one('hr.loan.type', 'Loan Type', tracking=True)
    depart_id = fields.Many2one('hr.department', 'Department', help='Department of employee')
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', 'Loan Lines', help='Settlements Table', tracking=True,
                                    copy=False)
    refuse_reason = fields.Text(tracking=True, copy=False)
    total_amount = fields.Float('Total Amount', digits='Payroll', readonly=True,
                                help='Amount of loan with interest rate', tracking=True, copy=False)
    amount = fields.Float(digits='Payroll')
    number_months = fields.Integer('Number of Months', help='Number of months to deduct the loan total amount',
                                   tracking=True, copy=False)
    is_generated = fields.Boolean('Generated', compute="_compute_is_generated")
    contract_id = fields.Many2one('hr.contract', 'Contract', readonly=True)
    payment_id = fields.Many2one('account.payment', 'Payment Order', copy=False)
    has_receipt_voucher = fields.Boolean(compute='_compute_has_receipt_voucher')
    balance = fields.Float(compute="_compute_balance", digits='Payroll', help='Remaining Amount')
    hr_admin = fields.Boolean("HR Admin", copy=False, compute="_compute_hr_admin",
                              default=lambda self: self.env.user.has_group("hr.group_hr_manager"))
    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Canceled'),
    ])

    @api.onchange('employee_id', 'amount', 'type_id')
    def on_change_amount(self):
        if self.approval_type == 'loan':
            contract = self.employee_id.contract_id
            total_amount = 0.0
            employee_salary = 0.0
            if self.employee_id:
                if not contract:
                    raise UserError(_('The Employee does not have valid contract'))

                employee_salary = contract.wage
                interest_rate = ((self.type_id.interest_rate) * 0.01)
                total_amount = self.amount + (self.amount * interest_rate)

            self.total_amount = total_amount

    def _compute_hr_admin(self):
        for rec in self:
            rec.hr_admin = self.env.user.has_group("hr.group_hr_manager")

    @api.depends('loan_line_ids')
    def _compute_is_generated(self):
        for rec in self:
            rec.is_generated = len(rec.loan_line_ids) > 0

    def _compute_has_receipt_voucher(self):
        for rec in self:
            rec.has_receipt_voucher = True if self.env['account.payment'].search([('loan_id', '=', rec.id),
                                                                                  ('payment_type', '=', 'inbound')],
                                                                                 limit=1) else False

    def _compute_balance(self):
        for rec in self:
            rec.balance = sum(rec.loan_line_ids.mapped('remaining_amount')) if rec.request_status == "approved" else 0

    @api.onchange("date_start", "number_months", 'type_id')
    def _get_date_end(self):
        if self.date_start and self.number_months:
            self.date_end = self.date_start + relativedelta(months=self.number_months)

    @api.onchange('employee_id')
    def on_change_employee(self):
        self.depart_id = self.employee_id.department_id.id
        self.contract_id = self.employee_id.contract_id.id if self.employee_id.contract_id else False

    @api.onchange('type_id')
    def on_change_type(self):
        self.number_months = self.type_id.months

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        for val in vals:
            if val["category_id"] == self.env.ref("hr_loan.approval_category_data_loan"):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                contract = employee.contract_id
                type_id = self.env["hr.loan.type"].browse(val.get('type_id', False))

                if contract:
                    # set total_amount for loan with interest rate
                    interest_rate = ((type_id.interest_rate) * 0.01) if type_id else 0
                    vals['total_amount'] = vals['amount'] + (vals['amount'] * interest_rate)
                else:
                    raise UserError(_('The Employee does not have valid contract'))
        res = super(ApprovalRequest, self).create(vals)
        loans = res.filtered(lambda x: x.approval_type == 'loan')
        loans.validation()
        loans.second_validation()
        loans.check_amount_totals()
        return res

    def write(self, vals):
        employee_obj = self.env['hr.employee']
        if vals.get("approval_type") == 'loan' or any(approval.approval_type == 'loan' for approval in self):
            for rec in self:
                employee = employee_obj.browse(vals.get('employee_id', False)) or rec.employee_id
                contract = employee.contract_id
                if not contract:
                    raise UserError(_('The Employee does not have valid contract'))
                if vals.get('loan_line_ids') or vals.get('amount'):
                    equel = rec.check_amount_totals()

                if vals.get('amount', False):
                    # set total_amount for loan with interest rate
                    type_id = self.env["hr.loan.type"].browse(vals.get('type_id', False)) if vals.get(
                        "type_id") else rec.type_id
                    interest_rate = ((type_id.interest_rate) * 0.01)
                    vals['total_amount'] = vals['amount'] + (vals['amount'] * interest_rate)

        res = super(ApprovalRequest, self).write(vals)
        loans = self.filtered(lambda x: x.approval_type == 'loan')
        loans.validation()
        loans.second_validation()
        loans.check_amount_totals()
        return res

    def unlink(self):
        for loan_request in self.filtered(lambda x: x.approval_type == 'loan' and x.payment_id):
            raise UserError(_('You Can not Delete Loan/s has Payment Order !'))
        return super(ApprovalRequest, self).unlink()

    def action_approve(self, approver=None):
        if self.approval_type == "loan":
            for rec in self:
                if not rec.loan_line_ids:
                    raise UserError(_('Please set number of months and populate settlements table !'))
                payment = rec.generate_payment()
                if self.company_id.reference_employee_in_journal_entries and not (
                        rec.employee_id.user_id or rec.employee_id.address_home_id):
                    raise UserError(
                        _("You cannot approve a loan record without linking the employee to a user or a private address!"))
                payment.partner_id = (rec.employee_id.user_id and rec.employee_id.user_id.partner_id) or \
                                     rec.employee_id.address_home_id
                rec.payment_id = payment.id
        return super(ApprovalRequest, self).action_approve(approver)

    def action_cancel(self):
        for rec in self.filtered(lambda x: x.approval_type == "loan"):
            if rec.payment_id.state == 'posted':
                raise UserError(
                    _('You can not cancel this loan, please contact accountant to cancel the payment order!'))
            rec.payment_id.unlink()
            for user in rec.approver_ids.mapped("user_id"):
                rec._get_user_approval_activities(user).unlink()
        return super(ApprovalRequest, self).action_cancel()

    def action_withdraw(self, approver=None):
        for rec in self.filtered(lambda x: x.approval_type == "loan"):
            if rec.payment_id.state == 'posted':
                raise UserError(
                    _('You can not cancel this loan, please contact accountant to cancel the payment order!'))
            rec.payment_id.unlink()
        return super(ApprovalRequest, self).action_withdraw(approver)

    def action_refuse(self, approver=None):
        for loan in self.filtered(lambda x: x.approval_type == 'loan'):
            if not loan.refuse_reason:
                raise UserError(_('Please set the refuse reason !'))
        return super(ApprovalRequest, self).action_refuse(approver)

    def clean_months(self):
        if self.request_status in ('new', 'pending'):
            self.loan_line_ids.unlink()
        else:
            raise UserError(_('Loan should not be submitted'))

    def generate_months(self):
        loan_line_obj = self.env['hr.loan.line']
        loan_amount = self.total_amount
        num_months = self.number_months
        loan_date = self.date
        first_date = self.date_start
        if not num_months:
            raise UserError(_('Set number of months to generate.'))

        if self.request_status not in ('new', 'pending'):
            raise UserError(_('Loan must be to submit or submitted.'))

        if not loan_amount:
            raise UserError(_('Set amount to generate.'))

        if not first_date:
            raise UserError(_('Set start date to generate.'))
        else:
            if first_date < loan_date:
                raise UserError(_('Start date must be after or equal of loan date.'))

        amount_per_month = loan_amount / num_months

        for i in range(0, num_months):
            date = first_date + relativedelta(months=i)
            vals = {'loan_id': self.id, 'discount_date': date, 'amount': amount_per_month}
            loan_line_obj.create(vals)
        lines_total = sum(self.mapped("loan_line_ids.amount"))
        x = loan_amount - lines_total
        self.loan_line_ids[-1].amount += x
        self.check_amount_totals()

    def generate_payment(self):
        default_journal_id = self.company_id.payment_journal.id
        vals = {'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_move_journal_types': ('bank', 'cash')}
        if default_journal_id:
            vals.update({'default_journal_id': default_journal_id})
        payment_form = Form(self.env['account.payment'].with_context(vals))
        payment_form.payment_type = "outbound"
        payment_form.date = self.date_confirmed
        payment_form.ref = 'Loan For ' + str(self.employee_id.name)
        payment_form.partner_type = 'supplier'
        payment_form.amount = self.total_amount
        payment_form.loan_id = self
        payment = payment_form.save()
        return payment

    def second_validation(self):
        for rec in self.filtered(lambda x: x.type_id.one_time_loan):
            res = self.search_count([('type_id', '=', rec.type_id.id), ('employee_id', '=', rec.employee_id.id),
                                     ('state', '=', 'approved')])
            if res > 1:
                raise UserError(_('This loan only once per service period!'))

    def validation(self):
        for rec in self:
            if rec.type_id.one_time_loan:
                if rec.employee_id.marital != 'single':
                    raise UserError(_('This loan eligible for single employees only!'))

                if rec.employee_id.gender != 'male':
                    raise UserError(_('This loan not eligible for females!'))

            if rec.contract_id.trial_date_end:
                if rec.date_start.date() <= rec.contract_id.trial_date_end:
                    raise UserError(_('The Employee not eligible for the loan in Trial Period Duration! '))
            else:
                return True

    def check_amount_totals(self):
        for loan_req in self.filtered(lambda x: x.loan_line_ids and x.amount):
            amount_total = sum(loan_req.mapped("loan_line_ids.amount"))
            precision = self.env['decimal.precision'].precision_get('Payroll')
            if not float_is_zero(abs(amount_total - loan_req.total_amount), precision):
                raise UserError(_('Total of Lines not equal to amount'))

# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import models


class HrPayslip(models.Model):
    """Inherits the model hr.payslip to add new functionalities"""
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        """Update the computing sheet of a payslip by adding loan details
        to the 'Other Inputs' section."""
        for data in self:
            if (not data.employee_id) or (not data.date_from) or (
                    not data.date_to):
                return
            loan_line = data.struct_id.rule_ids.filtered(
                lambda x: x.code == 'LO')
            if loan_line:
                get_amount = self.env['hr.loan'].search([
                    ('employee_id', '=', data.employee_id.id),
                    ('state', '=', 'approve')
                ], limit=1)
                # If there exist approved loan for the employee and not already
                # added to other input lines.
                if get_amount and (
                        'LO' not in data.input_line_ids.input_type_id.mapped(
                        'code')):
                    for lines in get_amount:
                        for line in lines.loan_line_ids:
                            if data.date_from <= line.date <= data.date_to:
                                if not line.paid:
                                    amount = line.amount
                                    name = loan_line.id
                                    data.input_data_line(name, amount, line)
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_done(self):
        """Mark loan as paid on paying payslip"""
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()

    def input_data_line(self, name, amount, loan):
        """Add loan details to payslip as other input"""
        check_lines = []
        new_name = self.env['hr.payslip.input.type'].search([
            ('input_id', '=', name)])
        line = (0, 0, {
            'input_type_id': new_name.id,
            'amount': amount,
            'name': 'LO',
            'loan_line_id': loan.id
        })
        check_lines.append(line)
        self.input_line_ids = check_lines

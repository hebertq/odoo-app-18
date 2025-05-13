# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class HrContract(models.Model):
    """Extends the 'hr.contract' model to add onchange methods to record
    changes in contract-related fields (wage, name, date_start, date_end) and
    stores the historical data in the 'salary.history' and 'contract.history'
    models for HR contracts."""
    _inherit = 'hr.contract'

    @api.onchange('wage')
    def _onchange_wage(self):
        """Create a record in 'salary.history' when the 'wage' field changes."""
        self.env['salary.history'].sudo().create([{
            'employee': self.employee_id.id,
            'employee_name': self.employee_id,
            'updated_date': fields.datetime.today(),
            'current_value': self.wage,
        }])

    @api.onchange('name')
    def _onchange_name(self):
        """Create a record in 'contract.history' when the 'name' field
        changes."""
        self.env['contract.history'].create([{
            'employee': self.employee_id.id,
            'employee_name': self.employee_id,
            'updated_date': fields.Date.today(),
            'changed_field': 'Contract Reference',
            'current_value': self.name,
        }])

    @api.onchange('date_start')
    def _onchange_date_start(self):
        """Create a record in 'contract.history' when the 'date_start' field
        changes."""
        self.env['contract.history'].create([{
            'employee': self.employee_id.id,
            'employee_name': self.employee_id,
            'updated_date': fields.Date.today(),
            'changed_field': 'Start Date',
            'current_value': self.date_start,
        }])

    @api.onchange('date_end')
    def _onchange_date_end(self):
        """Create a record in 'contract.history' when the 'date_end' field
        changes."""
        self.env['contract.history'].create([{
            'employee': self.employee_id.id,
            'employee_name': self.employee_id,
            'updated_date': fields.Date.today(),
            'changed_field': 'End Date',
            'current_value': self.date_end,
        }])

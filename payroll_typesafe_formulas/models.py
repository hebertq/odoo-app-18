# -*- coding: utf-8 -*-
# Copyright(c) João Jerónimo (written in 2020-2021)

from odoo import api, models, fields, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
#import pdb

class HrPayslipGeneralFormula(models.Model):
    _name = "hr.payslip.general.formula"
    _description = "Python formulas for calculating the custom fields of the PDF template. Several datatypes may be possible."
    
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    result_type = fields.Selection([
        ('float',   "Float"),
        ('int',     "Integer"),
        ('str',     "Text"),
        ], required=True)
    dependencies = fields.Char(string="Dependencies", help="Space-separated list of other formula codes that this formula depends on.")
    python_code = fields.Text(string="Python code to calculate value (assign output to 'result' variable)", required=True)
    
    def get_formula_value_for_payslip(self, rulecode, payslip):
        the_formula = self.search([('code', '=', rulecode)])
        if len(the_formula) != 1:
            raise ValidationError(_("The '%(formulacode)s' formula either does not exist or is duplicate.") % {
                'formulacode':      rulecode,
                })
        return the_formula.get_value_for_payslip(payslip)
    
    def get_value_for_payslip(self, payslip):
        self.ensure_one()
        # Helper classes (copied from hr_payroll_community):
        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # Declare and fill-in helper objects:
        categories_dict = {}
        for result_line in payslip.line_ids:
            # Get category code:
            categ_code = result_line.category_id.code
            # Get previous value:
            current_value = categories_dict.get(categ_code, 0)
            # Update it:
            categories_dict[categ_code] = current_value + result_line.total
        categories = BrowsableObject(payslip.employee_id.id, categories_dict, self.env)
        
        inputs_dict = {}
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        
        worked_days_dict = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        
        rules_dict = {}
        for result_line in payslip.line_ids:
            rules_dict[result_line.code] = result_line.salary_rule_id
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        
        # The hr_payslip code also puts the line totals as variables inside localdict, so we
        # need to replicate that behaviour for this to work:
        results_dict = {}
        for result_line in payslip.line_ids:
            results_dict[result_line.code] = result_line.total
        
        # Prepare environment:
        localdict = {
            'env':  self.env,
            'thispayslip':  payslip,
            
            'categories': categories,
            'rules': rules,
            'payslip': payslips,
            'worked_days': worked_days,
            'inputs': inputs,
            'employee': payslip.employee_id,    # Pronto
            'contract': payslip.contract_id,    # Pronto
            
            **results_dict
            }
        # Recursively call other formulas that this formula depends on:
        for depe in (self.dependencies or '').replace(",", " ").replace(";", " ").split():
            depe_obj = self.search([('code', '=', depe)])
            localdict[depe] = depe_obj.get_value_for_payslip(payslip)
        # Run the code:
        safe_eval(self.python_code, localdict, mode='exec', nocopy=True)
        # Check the return type:
        #result_type_obj = getattr(globals()['__builtins__'], self.result_type)  # Does not work
        result_type_obj = globals()['__builtins__'][self.result_type]  # Does not work
        assert(isinstance(result_type_obj, type))
        if not (isinstance(localdict['result'], result_type_obj)):
            raise ValidationError(_("The '%(formulaname)s' formula should have type '%(expectedtype)s' but returned type '%(returnedtype)s'.") % {
                'formulaname':      self.name,
                'expectedtype':     self.result_type,
                'returnedtype':     type(localdict['result']),
                })
        # Properly return the type-safe value:
        return localdict['result']

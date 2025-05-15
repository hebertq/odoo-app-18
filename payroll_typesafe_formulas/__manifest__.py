# -*- coding: utf-8 -*-
# Copyright(c) João Jerónimo (written in 2020-2021)
{
    'name': 'General Formula System for Payslips',
    'description': """
Introduction: Very simple formula system to help customize Payslip PDFs, type-safe.
Rationale: This module does not add any feature, but instead provides auxiliary support
for PDF templates to print payslips.
Suggested use case: Helps setting fields that appear on the generated PDF files.
""",
    'category': 'Human Resources',
    
    'author': 'João Jerónimo',
    'version': '15.0.1.0',
    'support': 'joao.jeronimo.pro@gmail.com',
    
    'application': False,
    'installable': True,
    
    'images': ['static/images/main_thumb.png'],
    
    # The license:
    'version': '18.0.1.0',
    'license': 'AGPL-3',
    
    'depends': [
        'hr_payroll_community',
        ],
    'data': [
        'ir.model.access.csv',
        'views.xml',
    ],
    'demo': [
        #'demo.xml',
        ],
}

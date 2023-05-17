# coding: utf-8
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mysql_account = fields.Boolean("MYSQL Config")
    localhost = fields.Char("Localhost",config_parameter='nhcl_rider_integration.localhost')
    mysqluser = fields.Char("MySql User",config_parameter='nhcl_rider_integration.mysqluser')
    mysqlpwd = fields.Char("MySql Password",config_parameter='nhcl_rider_integration.mysqlpwd')
    mysqldb = fields.Char("MySql DB",config_parameter='nhcl_rider_integration.mysqldb')
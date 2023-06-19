from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mysql_account = fields.Boolean("MYSQL Config")
    localhost = fields.Char("Localhost", config_parameter='rider_nhcl_integration.localhost')
    mysqluser = fields.Char("MySql User", config_parameter='rider_nhcl_integration.mysqluser')
    mysqlpwd = fields.Char("MySql Password", config_parameter='rider_nhcl_integration.mysqlpwd')
    mysqldb = fields.Char("MySql DB", config_parameter='rider_nhcl_integration.mysqldb')
    log_file_path = fields.Char("Log File Path", config_parameter='rider_nhcl_integration.log_file_path')

from odoo import models
from sqlalchemy import create_engine
from sqlalchemy import text

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def call_rider_account_payment(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        localhost = get_param('nhcl_rider_integration.localhost')
        mysqluser = get_param('nhcl_rider_integration.mysqluser')
        mysqlpwd = get_param('nhcl_rider_integration.mysqlpwd')
        mysqldb = get_param('nhcl_rider_integration.mysqldb')
        if mysqlpwd:
            engine = create_engine(f'mysql+pymysql://{mysqluser}:{mysqlpwd}@{localhost}/{mysqldb}')
        else:
            engine = create_engine(f'mysql+pymysql://{mysqluser}:@{localhost}/{mysqldb}')
        # engine = create_engine("mysql+pymysql://root:@localhost/rider_demo_db")
        with engine.connect() as connection:
            query = text("SELECT ID, Customer,Amount FROM accountpayment where Flag IS NULL")
            data = connection.execute(query)
            for (ID, Customer, Amount) in data:
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                payment_id = self.env['account.payment'].search(
                    [('partner_id', '=', customer_id.id), ('state', '=', 'draft')])
                if not payment_id:
                    if not customer_id:
                        vals = {
                            'name': Customer,
                        }
                        customer_id = self.env['res.partner'].create(vals)
                    self.env['account.payment'].create({'partner_id': customer_id.id, 'amount': Amount})
                    update_query = text("UPDATE accountpayment SET Flag=1 where Customer=Customer")
                    connection.execute(update_query)
            return data

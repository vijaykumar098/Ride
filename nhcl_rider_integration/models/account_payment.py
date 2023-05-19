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
                if Customer == None:
                    _logger.warning("Customer Name Must be Required to create a Account Payment for ID %s",ID)
                    continue
                if Amount == None:
                    _logger.warning("Amount Must be Greater than Zero for ID %s", ID)
                    continue
                if Amount and Amount <=0 :
                    _logger.warning("Amount Must be Greater than Zero for ID %s",ID)
                    continue
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                payment_id = self.env['account.payment'].search(
                    [('partner_id', '=', customer_id.id), ('state', '=', 'draft')])
                if not payment_id:
                    if not customer_id:
                        vals = {
                            'name': Customer,
                        }
                        customer_id = self.env['res.partner'].create(vals)
                    payment_id = self.env['account.payment'].create({'partner_id': customer_id.id, 'amount': Amount})
                    if payment_id:
                        update_query = text("UPDATE accountpayment SET Flag=1 where ID=ID")
                        connection.execute(update_query)
            return data

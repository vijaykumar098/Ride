from odoo import models
from sqlalchemy import create_engine
from sqlalchemy import text


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def call_rider_contact(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        localhost = get_param('nhcl_rider_integration.localhost')
        mysqluser = get_param('nhcl_rider_integration.mysqluser')
        mysqlpwd = get_param('nhcl_rider_integration.mysqlpwd')
        mysqldb = get_param('nhcl_rider_integration.mysqldb')
        if mysqlpwd:
            engine = create_engine(f'mysql+pymysql://{mysqluser}:{mysqlpwd}@{localhost}/{mysqldb}')
        else:
            engine = create_engine(f'mysql+pymysql://{mysqluser}:@{localhost}/{mysqldb}')
        # engine = create_engine("mysql+mysqldb://root:@localhost/rider_demo_db")
        with engine.connect() as connection:
            query = text(
                "SELECT ID, Name, Email, Phone, Street, Street2, City, State,  Zip, Country, Vat, Mobile, Property_Account_Receivable, Property_Account_Payable, Customer_Rank, Company, Company_Type FROM contact where Flag is NULL")
            data = connection.execute(query)
            for (ID, Name, Phone, Email, Street, Street2, City, State, Zip, Country, Vat, Mobile,
                 Property_Account_Receivable, Property_Account_Payable, Customer_Rank, Company, Company_Type) in data:
                if Name == None:
                    _logger.warning("Name Must be Required to create a customer for ID %s",ID)
                    continue
                if (Phone == None or Mobile == None) and Email == None:
                    _logger.warning("Phone/Mobile and Email Must be Required to create a customer for ID %s",ID)
                    continue
                if Property_Account_Payable == None:
                    _logger.warning("Account Payable Must be Required to create a customer for ID %s", ID)
                    continue
                if Property_Account_Receivable == None:
                    _logger.warning("Account Receivable Must be Required to create a customer for ID %s", ID)
                    continue
                if Mobile and len(Mobile)<10:
                    _logger.warning("Customer Not Created, Because %s Customer Mobile Number is Invalid. Please update it",Name)
                if Phone and len(Phone)<10:
                    _logger.warning("Customer Not Created, Because %s Customer Phone Number is Invalid. Please update it", Name)
                if (Mobile and len(Mobile)<10) or (Phone and len(Phone)<10):
                    continue
                country_id = self.env['res.country'].search([('name', '=', Country)])
                state_id = self.env['res.country.state'].search(
                    [('name', '=', State), ('country_id', '=', country_id.id)])
                partner = self.env['res.partner'].search(
                    [('name', '=', Name), ('phone', '=', Phone), ('email', '=', Email)])
                property_account_receivable_id = self.env['account.account'].search(
                    [('code', '=', Property_Account_Receivable)])
                property_account_payable_id = self.env['account.account'].search(
                    [('code', '=', Property_Account_Payable)])
                company_id = self.env['res.company'].search([('name', '=', Company)])
                if not partner:
                    vals = {
                        'name': Name,
                        'phone': Phone,
                        'email': Email,
                        'street': Street,
                        'street2': Street2,
                        'city': City,
                        'state_id': state_id.id,
                        'zip': Zip,
                        'country_id': country_id.id,
                        'vat': Vat,
                        'mobile': Mobile,
                        'property_account_receivable_id': property_account_receivable_id.id,
                        'property_account_payable_id': property_account_payable_id.id,
                        'customer_rank': Customer_Rank,
                        'company_id': company_id.id,
                        'company_type': Company_Type,
                    }
                    partner = self.env['res.partner'].create(vals)
                    if partner:
                        update_query = text("UPDATE contact SET Flag=1 where ID=ID")
                        connection.execute(update_query)
            self.env['account.move'].call_rider_account_move()
            self.env['account.payment'].call_rider_account_payment()
            return data

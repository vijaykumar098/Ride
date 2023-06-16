import time

import phonenumbers
from odoo import models, _
from sqlalchemy import create_engine
import logging
from datetime import datetime
import base64, os
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def call_mysql_connection(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        localhost = get_param('rider_nhcl_integration.localhost')
        mysqluser = get_param('rider_nhcl_integration.mysqluser')
        mysqlpwd = get_param('rider_nhcl_integration.mysqlpwd')
        mysqldb = get_param('rider_nhcl_integration.mysqldb')
        if localhost and mysqluser and mysqldb:
            if mysqlpwd:
                engine = create_engine(f'mysql+pymysql://{mysqluser}:{mysqlpwd}@{localhost}/{mysqldb}')
            else:
                engine = create_engine(f'mysql+pymysql://{mysqluser}:@{localhost}/{mysqldb}')
            with engine.connect() as connection:
                self.call_ride_sequence_functions(connection)
        else:
            raise UserError(_("Please Check the MySQL configuration in General Settings"))

    def call_ride_sequence_functions(self,connection):
        LOG_FILENAME = datetime.now().strftime(
            r'C:/Users/Administrator/Desktop/Navya/Rider Modules/Log/logfile_%H_%M_%S_%d_%m_%Y.log')
        mail_name = datetime.now().strftime('logfile_%H_%M_%S_%d_%m_%Y.log')
        file = logging.FileHandler(filename=LOG_FILENAME)
        file.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file.setFormatter(formatter)
        _logger.addHandler(file)
        with connection.begin():
            self.call_captain_contact(connection)
            self.call_rider_contact(connection)
            Product = None
            self.env['product.product'].call_rider_product_product(connection, LOG_FILENAME, Product)
            self.env['account.move'].call_captain_account_move(connection, LOG_FILENAME)
            self.env['account.move'].call_rider_account_move(connection, LOG_FILENAME)
            self.env['account.payment'].call_captain_account_payment(connection, LOG_FILENAME)
            self.env['account.payment'].call_rider_account_payment(connection, LOG_FILENAME)
            self.env['sale.order'].call_captain_subscription(connection, LOG_FILENAME)
            self.send_email_with_attachment(file, mail_name)
        # connection.commit()
        time.sleep(300)
        self.call_ride_sequence_functions(connection)

    def call_captain_contact(self, connection):
        captain_select_query = (
            "SELECT ID, Name, Mobile, Email, Street, Street2, City, State, Zip, Company, Customer_Rank, Company_Type FROM captain where Flag is NULL")
        captain_data = connection.execute(captain_select_query)
        _logger.info('Captain Contact Info')
        for (ID, Name, Mobile, Email, Street, Street2, City, State, Zip, Company, Customer_Rank,
             Company_Type) in captain_data:
            if Name == None:
                _logger.error(
                    "Failed to Create Contact With Name - %s",Name)
                continue
            if Mobile == None:
                _logger.error(
                    "Failed to Create Contact With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Mobile and (len(Mobile) != 10):
                _logger.error(
                    "Failed to Create Contact With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            partner_id = self.env['res.partner'].search([('name', '=', Name)])
            if partner_id and Mobile:
                partner_id = partner_id.check_valid_phone_number(Mobile)
            if not partner_id:
                state_id = self.env['res.country.state'].search([('name', '=', State)])
                property_account_receivable_id = self.env['account.account'].search([('account_type', '=', 'asset_receivable'),('reconcile', '=', True)])
                property_account_payable_id = self.env['account.account'].search([('account_type', '=', 'liability_payable'),('reconcile', '=', True)])
                company_id = self.env['res.company'].search([('name', '=', Company)])
                if not company_id:
                    company_id = self.env.user.company_id
                if not state_id:
                    state_id = self.env['res.country.state'].search([('country_id', '=', company_id.country_id.id)])
                vals = {
                    'name': Name,
                    'phone': Mobile,
                    'email': Email,
                    'street': Street,
                    'street2': Street2,
                    'city': City,
                    'state_id': state_id[0].id if state_id else False,
                    'zip': Zip,
                    'country_id': state_id[0].country_id.id if state_id else company_id.country_id.id,
                    'vat': '12AAAAA1234AAZA',
                    'mobile': Mobile,
                    'property_account_receivable_id': property_account_receivable_id[0].id if property_account_receivable_id else False,
                    'property_account_payable_id': property_account_payable_id.id,
                    'customer_rank': Customer_Rank,
                    'company_id': company_id.id,
                    'company_type': Company_Type,
                }
                partner_id = self.env['res.partner'].create(vals)
                if partner_id:
                    partner_id._onchange_mobile_validation()
                    partner_id._onchange_phone_validation()
                    captain_update_query = ("UPDATE captain SET Flag=1 where Name=%s and Mobile = %s")
                    c_vals = (partner_id.name, partner_id.mobile)
                    connection.execute(captain_update_query, c_vals)
                    _logger.info("Success to Create Contact With Name - %s and Mobile No. - %s", Name, Mobile)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Contacts Upto Date")
        return captain_data

    def call_rider_contact(self, connection):
        rider_select_query = (
            "SELECT ID, Name, Mobile, Email, Street, Street2, City, State, Zip, Company, Customer_Rank, Company_Type FROM rider where Flag is NULL")
        rider_data = connection.execute(rider_select_query)
        _logger.info('Rider Contact Info')
        for (ID, Name, Mobile, Email, Street, Street2, City, State, Zip, Company
             , Customer_Rank, Company_Type) in rider_data:
            if Name == None:
                _logger.error(
                    "Failed to Create Contact With Name - %s", Name)
                continue
            if Mobile == None:
                _logger.error(
                    "Failed to Create Contact With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Mobile and len(Mobile) != 10:
                _logger.error(
                    "Failed to Create Contact With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            partner_id = self.env['res.partner'].search([('name', '=', Name)])
            if partner_id and Mobile:
                partner_id = partner_id.check_valid_phone_number(Mobile)
            if not partner_id:
                state_id = self.env['res.country.state'].search([('name', '=', State)])
                property_account_receivable_id = self.env['account.account'].search([('account_type', '=', 'asset_receivable'),('reconcile', '=', True)])
                property_account_payable_id = self.env['account.account'].search([('account_type', '=', 'liability_payable'),('reconcile', '=', True)])
                company_id = self.env['res.company'].search([('name', '=', Company)])
                if not company_id:
                    company_id = self.env.user.company_id
                if not state_id:
                    state_id = self.env['res.country.state'].search([('country_id', '=', company_id.country_id.id)])
                vals = {
                    'name': Name,
                    'phone': Mobile,
                    'email': Email,
                    'street': Street,
                    'street2': Street2,
                    'city': City,
                    'state_id': state_id[0].id if state_id else False,
                    'zip': Zip,
                    'country_id': state_id[0].country_id.id if state_id else company_id.country_id.id,
                    'vat': '12AAAAA1234AAZA',
                    'mobile': Mobile,
                    'property_account_receivable_id': property_account_receivable_id[0].id if property_account_receivable_id else False,
                    'property_account_payable_id': property_account_payable_id.id,
                    'customer_rank': Customer_Rank,
                    'company_id': company_id.id,
                    'company_type': Company_Type,
                }
                partner_id = self.env['res.partner'].create(vals)
                if partner_id:
                    partner_id._onchange_mobile_validation()
                    partner_id._onchange_phone_validation()
                    rider_update_query = ("UPDATE rider SET Flag=1 where Name=%s and Mobile = %s")
                    r_vals = (partner_id.name, partner_id.mobile)
                    connection.execute(rider_update_query, r_vals)
                    _logger.info("Success to Create Contact With Name - %s and Mobile No. - %s", Name, Mobile)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Contacts Upto Date")
        return rider_data

    def send_email_with_attachment(self, LOG_FILENAME, Mail_Name):
        group_model_id = self.env['ir.model']._get('res.partner')
        partner_id = self.env['res.users'].browse(2).partner_id
        template_id = self.env['mail.template'].search(
            [('model_id', '=', group_model_id.id), ('subject', '=', 'Log Data')])
        body_html = '''Logger Info for Contact, Service, Invoice and Payment'''
        if not template_id:
            template_data = {
                'model_id': group_model_id.id,
                'name': 'Log Template',
                'subject': Mail_Name,
                'body_html': body_html,
                'email_from': self.env.user.email,
                'email_to': partner_id.email,
            }
            template_id = self.env['mail.template'].create(template_data)
        path = os.path.expanduser(LOG_FILENAME.baseFilename)
        file = open(path, "rb")
        out = file.read()
        file.close()
        gentextfile = base64.b64encode(out)
        ir_values = {
            'name': Mail_Name,
            'type': 'binary',
            'store_fname': path,
            'datas': gentextfile,
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        template_id.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {'email_to': partner_id.email,
                        'email_from': self.env.user.email}
        template_id.send_mail(partner_id.id, email_values=email_values, force_send=True)
        template_id.attachment_ids = [(3, data_id.id)]
        return True

    def check_valid_phone_number(self, Mobile):
        m = phonenumbers.parse(self.mobile,self.country_id.code)
        if not m.country_code:
            return self
        if str(m.national_number) == Mobile:
            customer_id = self
        else:
            customer_id = self.env['res.partner']
        return customer_id

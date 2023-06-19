import logging,re
from odoo import models
import phonenumbers
from sqlalchemy import create_engine,text
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    #####  cp = captain_payment

    def call_captain_account_payment(self, connection, LOG_FILENAME):
        cp_select_query = text("SELECT ID, Customer, Mobile, Ref, Amount FROM captain_payment where Flag IS NULL")
        cp_data = connection.execute(cp_select_query)
        file_handler = logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
        _logger.setLevel(logging.DEBUG)
        _logger.info('Captain Payment Info')
        for (ID, Customer, Mobile, Ref, Amount) in cp_data:
            if Ref == None:
                _logger.error("Failed to create a Payment with Ref - %s", Ref)
                continue
            if Mobile == None:
                _logger.error(
                    "Failed to Search Customer With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Mobile and (len(Mobile) != 10):
                _logger.error(
                    "Failed to Search Customer With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Customer == None:
                _logger.error("Failed to Create Payment With Customer - %s", Customer)
                continue
            customer_id = self.env['res.partner'].search([('name', '=', Customer)])
            if customer_id and Mobile:
                customer_id = customer_id.check_valid_phone_number(Mobile)
            if not customer_id:
                self.env['res.partner'].call_captain_contact(connection)
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                if customer_id and Mobile:
                    customer_id = customer_id.check_valid_phone_number(Mobile)
                if not customer_id:
                    _logger.error("Failed to Search Customer with Name - %s  and Mobile - %s in Existing Contacts", Customer,
                                  Mobile)
                    continue
            payment_id = self.env['account.payment'].search([('partner_id', '=', customer_id.id), ('ref', '=', Ref)])
            if not payment_id:
                company_id = self.env['res.company'].search([('id', '=', customer_id.company_id.id)])
                payment_id = self.env['account.payment'].create(
                    {'partner_id': customer_id.id, 'ref': Ref, 'currency_id': company_id.currency_id.id,
                     'amount': Amount})
                if payment_id:
                    cp_update_query = text("UPDATE captain_payment SET Flag=1 where Ref=%s and Mobile=%s and Customer=%s")
                    cp_vals = (payment_id.ref, payment_id.partner_id.mobile, payment_id.partner_id.name)
                    connection.execute(cp_update_query, cp_vals)
                    _logger.info("Success to Create Payment With Customer - %s and Ref - %s", Customer, Ref)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Payments Upto Date")
        return cp_data

    #####  rp = rider_payment

    def call_rider_account_payment(self, connection, LOG_FILENAME):
        rp_select_query = text("SELECT ID, Customer, Mobile, Ref, Amount FROM  rider_payment where Flag IS NULL")
        rp_data = connection.execute(rp_select_query)
        _logger.info('Rider Payment Info')
        for (ID, Customer, Mobile, Ref, Amount) in rp_data:
            if Ref == None:
                _logger.error("Failed to create Payment with Ref - %s", Ref)
                continue
            if Mobile == None:
                _logger.error(
                    "Failed to Search Customer With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Mobile and (len(Mobile) != 10):
                _logger.error(
                    "Failed to Search Customer With Mobile No. - %s, Because Mobile No. length must be equal to 10 Chars",
                    Mobile)
                continue
            if Customer == None:
                _logger.error("Failed to Create Payment With Customer - %s", Customer)
                continue
            customer_id = self.env['res.partner'].search([('name', '=', Customer)])
            if customer_id and Mobile:
                customer_id = customer_id.check_valid_phone_number(Mobile)
            if not customer_id:
                self.env['res.partner'].call_rider_contact(connection)
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                if customer_id and Mobile:
                    customer_id = customer_id.check_valid_phone_number(Mobile)
                if not customer_id:
                    _logger.error("Failed to Search Contact with Name - %s  and Mobile - %s in Existing Contacts", Customer,
                                  Mobile)
                    continue
            payment_id = self.env['account.payment'].search([('partner_id', '=', customer_id.id), ('ref', '=', Ref)])
            if not payment_id:
                company_id = self.env['res.company'].search([('id', '=', customer_id.company_id.id)])
                payment_id = self.env['account.payment'].create(
                    {'partner_id': customer_id.id, 'ref': Ref, 'currency_id': company_id.currency_id.id,
                     'amount': Amount})
                if payment_id:
                    rp_update_query = text("UPDATE rider_payment SET Flag=1 where Ref=%s and Mobile=%s and Customer=%s")
                    rp_vals = (payment_id.ref, payment_id.partner_id.mobile, payment_id.partner_id.name)
                    connection.execute(rp_update_query, rp_vals)
                    _logger.info("Success to Create Payment With Customer - %s and Ref - %s", Customer, Ref)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Payments Upto Date")
        return rp_data

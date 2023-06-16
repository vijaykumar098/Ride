import logging
from odoo import models, fields
from sqlalchemy import create_engine
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ######  ci = captain_invoice

    def call_captain_account_move(self, connection, LOG_FILENAME):
        ci_select_query = (
            "SELECT ID, Customer, Ref, Mobile, Product, Price_Unit, Discount FROM captain_invoice where Flag IS NULL")
        ci_data = connection.execute(ci_select_query)
        file_handler = logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
        _logger.setLevel(logging.DEBUG)
        _logger.info('Captain Invoice Info')
        for (
                ID, Customer, Ref, Mobile, Product, Price_Unit, Discount) in ci_data:
            if Ref == None:
                _logger.error("Failed to create Invoice with Ref - %s", Ref)
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
                _logger.error("Failed to Search Customer With Name - %s", Customer)
                continue
            if Product == None:
                _logger.error("Failed to Search Product With Name - %s", Product)
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
                    _logger.error("Failed to Search Customer With Name - %s and Mobile - %s in Existing Contacts",
                                  Customer, Mobile)
                    continue
            product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
            if not product_id:
                self.env['product.product'].call_rider_product_product(connection, LOG_FILENAME, Product)
                product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
                if not product_id:
                    _logger.error(
                        "Failed to Search Product With Name - %s in Existing Products", Product)
                    continue
            move_id = self.env['account.move'].search([('partner_id', '=', customer_id.id), ('ref', '=', Ref)])
            line_account_id = self.env['account.account'].search([('account_type', '=', 'income')])
            if not move_id:
                journal_id = self.env['account.journal'].search([('type', '=', 'sale')])
                product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
                vals = {
                    'partner_id': customer_id.id,
                    'invoice_date': fields.Date.today(),
                    'journal_id': journal_id.id,
                    'l10n_in_state_id': customer_id.state_id.id,
                    'move_type': 'out_invoice',
                    'ref': Ref,
                }
                move_id = self.env['account.move'].create(vals)
            move_line_id = self.env['account.move.line'].search(
                [('move_id', '=', move_id.id), ('product_id', '=', product_id.id)])
            if not move_line_id:
                move_lines = {
                    'product_id': product_id.id,
                    'name': product_id.name,
                    'account_id': product_id.categ_id.property_account_income_categ_id.id if product_id.categ_id.property_account_income_categ_id else line_account_id.id,
                    'quantity': 1,
                    'product_uom_id': product_id.uom_id.id,
                    'price_unit': Price_Unit,
                    'move_id': move_id.id,
                    'discount': Discount,
                }
                line = self.env['account.move.line'].create(move_lines)
                line.tax_ids = False
                line.tax_ids = product_id.taxes_id
                if line:
                    ci_line_update_query = ("UPDATE captain_invoice SET Flag=1 where Customer=%s and Ref=%s")
                    ci_l_vals = (move_id.partner_id.name, move_id.ref)
                    connection.execute(ci_line_update_query, ci_l_vals)
                    _logger.info("Success to Create Invoice with Customer - %s and Ref - %s", Customer, Ref)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Invoices Upto Date")
        return ci_data

    ######  ri = rider_invoice

    def call_rider_account_move(self, connection, LOG_FILENAME):
        ri_select_query = (
            "SELECT ID, Customer, Ref, Mobile, Product, Price_Unit, Discount FROM rider_invoice where Flag IS NULL")
        ri_data = connection.execute(ri_select_query)
        _logger.info('Rider Invoice Info')
        for (
                ID, Customer, Ref, Mobile, Product, Price_Unit, Discount) in ri_data:
            if Ref == None:
                _logger.error("Failed to create Invoice with Ref -  %s", Ref)
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
                _logger.error("Failed to Search Customer With Name - %s", Customer)
                continue
            if Product == None:
                _logger.error("Failed to Search Product With Name - %s", Product)
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
                    _logger.error("Failed to Search Customer With Name - %s and Mobile - %s in Existing Contacts",
                                  Customer,
                                  Mobile)
                    continue
            product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
            if not product_id:
                self.env['product.product'].call_rider_product_product(connection, LOG_FILENAME, Product)
                product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
                if not product_id:
                    _logger.error(
                        "Failed to Search Product With Name - %s in Existing Products", Product)
                    continue
            move_id = self.env['account.move'].search([('partner_id', '=', customer_id.id), ('ref', '=', Ref)])
            line_account_id = self.env['account.account'].search([('account_type', '=', 'income')])
            if not move_id:
                journal_id = self.env['account.journal'].search([('type', '=', 'sale')])
                product_id = self.env['product.product'].search([('name', '=', Product), ('active', '=', True)])
                vals = {
                    'partner_id': customer_id.id,
                    'invoice_date': fields.Date.today(),
                    'journal_id': journal_id.id,
                    'l10n_in_state_id': customer_id.state_id.id,
                    'move_type': 'out_invoice',
                    'ref': Ref,
                }
                move_id = self.env['account.move'].create(vals)
            move_line_id = self.env['account.move.line'].search(
                [('move_id', '=', move_id.id), ('product_id', '=', product_id.id)])
            if not move_line_id:
                move_lines = {
                    'product_id': product_id.id,
                    'name': product_id.name,
                    'account_id': product_id.categ_id.property_account_income_categ_id.id if product_id.categ_id.property_account_income_categ_id else line_account_id.id,
                    'quantity': 1,
                    'product_uom_id': product_id.uom_id.id,
                    'price_unit': Price_Unit,
                    'move_id': move_id.id,
                    'discount': Discount,
                }
                line = self.env['account.move.line'].create(move_lines)
                line.tax_ids = False
                line.tax_ids = product_id.taxes_id
                if line:
                    ri_line_update_query = ("UPDATE rider_invoice SET Flag=1 where Customer=%s and Ref=%s")
                    ri_l_vals = (move_id.partner_id.name, move_id.ref)
                    connection.execute(ri_line_update_query, ri_l_vals)
                    _logger.info("Success to Create Invoice with Customer - %s and Ref - %s", Customer, Ref)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Invoices Upto Date")
        return ri_data

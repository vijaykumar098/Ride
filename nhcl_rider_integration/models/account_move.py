from odoo import models, fields
from sqlalchemy import create_engine
from sqlalchemy import text


class AccountMove(models.Model):
    _inherit = 'account.move'

    def call_rider_account_move(self):
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
                "SELECT ID, Customer, Journal, Company, State, State_Code, Move_Type, Ref, Partner_Bank, Currency, Country, Product, Account, Quantity, Product_Uom, Price_Unit, Discount, Tax_Ids FROM invoice where Flag IS NULL")
            data = connection.execute(query)
            for (
                    ID, Customer, Journal, Company, State, State_Code, Move_Type, Ref, Partner_Bank, Currency, Country,
                    Product,
                    Account, Quantity, Product_Uom, Price_Unit, Discount, Tax_Ids) in data:
                if Customer == None:
                    _logger.warning("Customer Name Must be Required to create a Invoice for ID %s",ID)
                    continue
                if Product == None:
                    _logger.warning("Product Must be Required to create a Invoice for ID %s",ID)
                    continue
                if Account == None:
                    _logger.warning("Account Must be Required to create a Invoice for ID %s",ID)
                    continue
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                if State == None:
                    if customer_id.state_id:
                        State = customer_id.state_id.name
                    else:
                        _logger.warning("State Must be Required to create a Invoice for ID %s", ID)
                        continue
                if Company == None:
                    if customer_id.company_id:
                        Company = customer_id.company_id.name
                    else:
                        _logger.warning("Company Must be Required to create a Invoice for ID %s", ID)
                        continue
                if Move_Type == None:
                    _logger.warning("Move Type Must be Required to create a Invoice for ID %s",ID)
                    continue
                company_id = self.env['res.company'].search([('name', '=', Company)])
                journal_id = self.env['account.journal'].search([('type', '=', 'sale')])
                partner_bank_id = self.env['account.account'].search([('code', '=', Partner_Bank)])
                account_id = self.env['account.account'].search([('code', '=', Account)])
                if Currency == None:
                    if company_id.currency_id:
                        Currency = company_id.currency_id.name
                    else:
                        _logger.warning("Currency Must be Required to create a Invoice for ID %s", ID)
                        continue
                currency_id = self.env['res.currency'].search([('name', '=', Currency)])
                product_uom_id = self.env['uom.uom'].search([('name', '=', Product_Uom)])
                tax_ids = self.env['account.tax'].search([('name', '=', Tax_Ids), ('type_tax_use', '=', 'sale')])
                state_id = self.env['res.country.state']
                if State:
                    state_id = self.env['res.country.state'].search([('name', '=', State)])
                product_id = self.env['product.product'].search([('name', '=', Product)])
                if not customer_id:
                    customer_id = self.env['res.partner'].create({'name': Customer})
                if not product_id:
                    product_id = self.env['product.product'].create({'name': Product})
                move_id = self.env['account.move'].search([('partner_id', '=', customer_id.id), ('state', '=', 'draft'),
                                                           ('l10n_in_state_id', '=', state_id.id)])
                if not move_id:
                    vals = {
                        'partner_id': customer_id.id,
                        'invoice_date': fields.Date.today(),
                        'journal_id': journal_id.id,
                        'company_id': company_id.id,
                        'l10n_in_state_id': state_id.id,
                        'move_type': Move_Type,
                        'ref': Ref,
                        'partner_bank_id': partner_bank_id.id,
                        'currency_id': currency_id.id,
                    }
                    move_id = self.env['account.move'].create(vals)
                    update_query = text("UPDATE invoice SET Flag=1 where ID=ID")
                    connection.execute(update_query)
                move_line_id = self.env['account.move.line'].search(
                    [('move_id', '=', move_id.id), ('product_id', '=', product_id.id)])
                if not move_line_id:
                    move_lines = {
                        'product_id': product_id.id,
                        'name': product_id.name,
                        'account_id': account_id.id,
                        'quantity': Quantity,
                        'product_uom_id': product_uom_id.id,
                        'price_unit': Price_Unit,
                        'move_id': move_id.id,
                        'discount': Discount,
                        'company_id': company_id.id,
                        # 'tax_ids': tax_ids,
                    }
                    line = self.env['account.move.line'].create(move_lines)
                    line.tax_ids = False
                    line.tax_ids = tax_ids
                    if line:
                        line_query = text("UPDATE invoice SET Flag=1 where ID=ID")
                        connection.execute(line_query)
            return data

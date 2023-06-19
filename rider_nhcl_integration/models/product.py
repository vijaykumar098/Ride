import logging
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def call_rider_product_product(self, connection, LOG_FILENAME,Product):
        if Product != None:
            service_select_query = ("SELECT ID, Name, Internal_Ref, Company, Invoice_Policy, Service_Policy FROM service where Name='" + Product + "'")
            service_data = connection.execute(service_select_query)
        else:
            service_select_query = (
                "SELECT ID, Name, Internal_Ref, Company, Invoice_Policy, Service_Policy FROM service where Flag IS NULL")
            service_data = connection.execute(service_select_query)
            file_handler = logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)
            _logger.setLevel(logging.DEBUG)
        _logger.info('Service Info')
        for (ID, Name, Internal_Ref, Company, Invoice_Policy, Service_Policy) in service_data:
            if Name == None:
                _logger.error(
                    "Failed to Create Product with Name - %s, Because Name Must be Required to create a Product", Name)
                continue
            if Internal_Ref == None:
                _logger.error(
                    "Failed to Create Product with Name - %s , Because Internal_Ref Must be Required to create a Product", Name)
                continue
            product = self.env['product.product'].search([('name', '=', Name), ('default_code', '=', Internal_Ref)])
            if not product:
                company_id = self.env['res.company'].search([('name', '=', Company)])
                tax = self.env['account.tax'].search([('name', '=', 'Sales Tax 18%'), ('type_tax_use', '=', 'sale')])
                vals = {
                    'name': Name,
                    'default_code': Internal_Ref,
                    'detailed_type': 'service',
                    'company_id': company_id.id,
                    'invoice_policy': Invoice_Policy,
                    'service_policy': Service_Policy,
                    'recurring_invoice': True,
                    'sale_ok': 1,
                    'taxes_id': tax,
                }
                product_id = self.env['product.product'].create(vals)
                if product_id:
                    service_update_query = ("UPDATE service SET Flag=1 where Internal_Ref=%s and Name=%s")
                    s_vals = (product_id.default_code, product_id.name)
                    connection.execute(service_update_query, s_vals)
                    _logger.info("Success to Create Product with Name - %s and Internal_Ref - %s",Name,Internal_Ref)
                    self.env.cr.commit()
        else:
            _logger.info("Nothing to Create, All the Products Upto Date")
        return service_data

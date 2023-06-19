from odoo import models, _, api, fields
import logging
_logger = logging.getLogger(__name__)
from odoo.tests import Form
from sqlalchemy import create_engine, text

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    workflow_process_id = fields.Many2one("automatic.sale.workflow.process",string="Automatic Sale Workflow")

    ##### cs = captain_subscription

    def call_captain_subscription(self, connection,LOG_FILENAME):
        cs_select_query = text(
            "SELECT ID, Customer, Mobile, Subscription_Plan FROM captain_subscription where Flag IS NULL")
        cs_data = connection.execute(cs_select_query)
        file_handler = logging.FileHandler(LOG_FILENAME, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
        _logger.setLevel(logging.DEBUG)
        _logger.info('Captain Subscription Info')
        for (
                ID, Customer, Mobile, Subscription_Plan) in cs_data:
            if Customer == None:
                _logger.error("Failed to Search Customer With Name - %s", Customer)
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
            if Subscription_Plan == None:
                _logger.error("Failed to Search Subscription Plan With Name - %s", Subscription_Plan)
                continue
            customer_id = self.env['res.partner'].search([('name', '=', Customer)])
            if customer_id and Mobile:
                customer_id = customer_id.check_valid_phone_number(Mobile)
            if not customer_id:
                self.env['res.partner'].call_captain_contact(connection)
                self.env['res.partner'].call_rider_contact(connection)
                customer_id = self.env['res.partner'].search([('name', '=', Customer)])
                if customer_id and Mobile:
                    customer_id = customer_id.check_valid_phone_number(Mobile)
                if not customer_id:
                    _logger.error("Failed to Search Customer With Name - %s and Mobile - %s in Existing Contacts", Customer,
                                  Mobile)
                    continue
            sale_order_template_id = self.env['sale.order.template'].search([('name', '=', Subscription_Plan)])
            sale_workflow_process = self.env['automatic.sale.workflow.process'].search([])
            if not sale_workflow_process:
                sale_workflow_process = self.env["automatic.sale.workflow.process"].create({'name':"Automatic",'validate_order':True})
            vals = {
                'partner_id': customer_id.id,
                'sale_order_template_id': sale_order_template_id.id,
                'workflow_process_id': sale_workflow_process.id
            }
            sale_order_id = self.env['sale.order'].create(vals)
            if sale_order_id:
                cs_move_update_query = ("UPDATE captain_subscription SET Flag=1 where Customer='%s' and Subscription_Plan='%s' and Mobile = '%s'")
                cs_m_vals = (sale_order_id.partner_id.name,sale_order_id.sale_order_template_id.name,sale_order_id.partner_id.mobile)
                connection.execute(text(cs_move_update_query %cs_m_vals))
                self.env.cr.commit()
                _logger.info("Success to Create Subscription With Customer - %s and  Mobile - %s and Subscription_Plan - %s", Customer, Mobile, Subscription_Plan)
                sale_order_id._onchange_sale_order_template_id()
                # sale_order_id.order_line._onchange_product_id()
                sale_workflow_process.auto_confirm(sale_order_id)

        else:
            _logger.info("Nothing to Create, All the Subscriptions Upto Date")
        return cs_data

    def _create_invoices(self, grouped=False, final=False, date=None):
        for order in self:
            for line in order.order_line:
                if line.qty_delivered_method == "manual" and not line.qty_delivered:
                    line.write({"qty_delivered": line.product_uom_qty})
        return super()._create_invoices(grouped=grouped, final=final, date=date)


import logging
from contextlib import contextmanager

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


@contextmanager
def savepoint(cr):
    """Open a savepoint on the cursor, then yield.

    Warning: using this method, the exceptions are logged then discarded.
    """
    try:
        with cr.savepoint():
            yield
    except Exception:
        _logger.exception("Error during an automatic workflow action.")


class AutomaticSaleWorkflowProcess(models.Model):
    """Scheduler that will play automatically the validation of
    invoices, pickings..."""

    _name = "automatic.sale.workflow.process"
    _description = (
        "Scheduler that will play automatically the validation of"
        " invoices, pickings..."
    )

    name = fields.Char(required=True)
    validate_order = fields.Boolean()

    def _do_send_order_confirmation_mail(self, sale):
        """Send order confirmation mail, while filtering to make sure the order is
        confirmed with _do_validate_sale_order() function"""
        if not self.env["sale.order"].search_count([("id", "=", sale.id), ("state", "=", "sale")]):
            return
        if sale.user_id:
            sale = sale.with_user(sale.user_id)
        sale._send_order_confirmation_mail()

    @api.model
    def _validate_sale_orders(self, sale):
        with savepoint(self.env.cr):
            sale.action_confirm()
            self._do_send_order_confirmation_mail(sale)

    def _do_create_invoice(self, sale):
        """Create an invoice for a sales order, filter ensure no duplication"""
        payment = self.env["sale.advance.payment.inv"].create(
            {"sale_order_ids": sale.ids}
        )
        payment.with_context(active_model="sale.order").create_invoices()

    @api.model
    def _create_invoices(self, sales):
        for sale in sales:
            with savepoint(self.env.cr):
                self._do_create_invoice(sale)

    def _do_validate_invoice(self, invoice):
        """Validate an invoice, filter ensure no duplication"""
        invoice.with_company(invoice.company_id).action_post()

    @api.model
    def _validate_invoices(self, invoice_ids):
        for invoice in invoice_ids:
            with savepoint(self.env.cr):
                self._do_validate_invoice(invoice)

    def _do_validate_picking(self, picking):
        picking.validate_picking()

    @api.model
    def _validate_pickings(self, picking_ids):
        for picking in picking_ids:
            with savepoint(self.env.cr):
                self._do_validate_picking(picking)

    def _do_sale_done(self, sale):
        sale.action_done()

    @api.model
    def _sale_done(self, sales):
        for sale in sales:
            with savepoint(self.env.cr):
                self._do_sale_done(sale)

    def _prepare_dict_account_payment(self, invoice):
        partner_type = (
                invoice.move_type in ("out_invoice", "out_refund")
                and "customer"
                or "supplier"
        )
        return {
            "reconciled_invoice_ids": [(6, 0, invoice.ids)],
            "amount": invoice.amount_residual,
            "partner_id": invoice.partner_id.id,
            "partner_type": partner_type,
            "date": fields.Date.context_today(self),
        }

    @api.model
    def _register_payments(self, invoice_ids):
        for invoice in invoice_ids:
            with savepoint(self.env.cr):
                self._register_payment_invoice(invoice)
        return

    def _register_payment_invoice(self, invoice):
        payment = self.env["account.payment"].create(
            self._prepare_dict_account_payment(invoice)
        )
        payment.action_post()

        domain = [
            ("account_type", "in", ("asset_receivable", "liability_payable")),
            ("reconciled", "=", False),
        ]
        payment_lines = payment.line_ids.filtered_domain(domain)
        lines = invoice.line_ids
        for account in payment_lines.account_id:
            (payment_lines + lines).filtered_domain(
                [("account_id", "=", account.id), ("reconciled", "=", False)]
            ).reconcile()

    def auto_confirm(self, sale):
        self._validate_sale_orders(sale)
        self.env.cr.commit()
        # if sale.picking_ids:
        #     self._validate_pickings(sale.picking_ids)
        self._create_invoices(sale)
        self.env.cr.commit()
        if sale.invoice_ids:
            self._validate_invoices(sale.invoice_ids)
        self.env.cr.commit()
        self._sale_done(sale)
        self.env.cr.commit()
        if sale.invoice_ids:
            self._register_payments(sale.invoice_ids)

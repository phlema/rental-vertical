# Part of rental-vertical See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductTimeline(models.Model):
    _inherit = "product.timeline"

    type = fields.Selection(
        selection_add=[
            ("delivery", "Delivery"),
        ],
    )

    freight_forwarder_id = fields.Many2one(
        "res.partner",
        "Freight forwarder",
        ondelete="set null",
        compute="_compute_fields",
    )

    freight_forwarder_name = fields.Char(
        compute="_compute_fields",
    )

    source_address = fields.Char(
        "Shipping address",
        compute="_compute_fields",
    )

    destination_address = fields.Char(
        "Shipping address",
        compute="_compute_fields",
    )

    @api.multi
    def _compute_fields(self):
        super(ProductTimeline, self)._compute_fields()
        lang = self.env["res.lang"].search([("code", "=", self.env.user.lang)])
        for line in self:
            if line.res_model == "purchase.order.line":
                obj = self.env[line.res_model].browse(line.res_id)
                order_obj = obj.order_id

                line.name = (
                    _("T: %s") % order_obj.partner_id.name
                    if order_obj.partner_id
                    else obj.name
                )
                line.order_name = order_obj.name
                line.freight_forwarder_id = order_obj.partner_id.id
                line.source_address = (
                    obj.trans_origin_sale_line_id.planned_source_address_id._display_address()
                )
                line.destination_address = (
                    obj.trans_origin_sale_line_id.order_id.partner_shipping_id._display_address()
                )

                line.currency_id = obj.currency_id.id
                line.amount = "{price_subtotal} {currency}".format(
                    price_subtotal=lang.format(
                        "%.2f", line.price_subtotal, grouping=True
                    ),
                    currency=line.currency_id.symbol,
                )

            line.freight_forwarder_name = line.freight_forwarder_id.display_name

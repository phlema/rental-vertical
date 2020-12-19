# Part of rental-vertical See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class ProductTimeline(models.Model):
    _inherit = "product.timeline"

    product_instance_state = fields.Selection(
        related="product_id.instance_state",
    )

    product_instance_state_formated = fields.Char(
        compute="_compute_fields",
    )

    product_instance_next_service_date = fields.Date(
        related="product_id.instance_next_service_date",
    )

    product_instance_current_location_id = fields.Many2one(
        related="product_id.instance_current_location_id",
    )

    product_instance_current_location_name = fields.Char(
        compute="_compute_fields",
    )

    product_instance_serial_number_id = fields.Many2one(
        related="product_id.instance_serial_number_id",
    )

    product_instance_serial_number_name = fields.Char(
        compute="_compute_fields",
    )

    @api.multi
    def _compute_fields(self):
        super(ProductTimeline, self)._compute_fields()
        for line in self:
            line.product_instance_serial_number_name = (
                line.product_instance_serial_number_id.display_name
            )
            line.product_instance_current_location_name = (
                line.product_instance_current_location_id.display_name
            )

            try:
                selections = self.fields_get()["product_instance_state"]["selection"]
                selection = [
                    s for s in selections if s[0] == line.product_instance_state
                ][0]
                line.product_instance_state_formated = selection[1]
            except Exception as e:
                _logger.exception(e)
                line.product_instance_state_formated = str(line.product_instance_state)

    @api.multi
    @api.constrains("date_start", "date_end")
    def _check_date(self):
        for line in self:
            if line.type in ["rental", "reserved"]:
                domain = [
                    ("date_start", "<", line.date_end),
                    ("date_end", ">", line.date_start),
                    ("product_id", "=", line.product_id.id),
                    ("product_id.product_instance", "=", True),
                    ("type", "in", ["rental", "reserved"]),
                    ("id", "!=", line.id),
                ]
                lines = self.search_count(domain)
                if lines:
                    msg = _(
                        "You can not have 2 timelines that overlaps on the same day."
                    )
                    raise exceptions.ValidationError(msg)

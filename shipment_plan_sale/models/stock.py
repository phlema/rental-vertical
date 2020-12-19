# Part of rental-vertical See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models, exceptions, _
import logging

logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    shipment_plan_id = fields.Many2one(
        "shipment.plan",
        "Shipment Plan",
        ondelete="set null",
    )

    @api.constrains("shipment_plan_id")
    def check_shipment_plan_id(self):
        """
        One Picking can only have one Shipment Plan
        """
        if self.shipment_plan_id:
            res = self.search_count(
                [
                    ("picking_id", "=", self.picking_id.id),
                    ("shipment_plan_id", "!=", False),
                    ("shipment_plan_id", "!=", self.shipment_plan_id.id),
                    ("id", "!=", self.id),
                ]
            )
            if res > 0:
                raise exceptions.ValidationError(
                    _("Requested by must be equal to the order")
                )


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipment_plan_id = fields.Many2one(
        "shipment.plan",
        "Shipment Plan",
        compute="_compute_shipment_plan_id",
    )

    @api.multi
    def _compute_shipment_plan_id(self):
        for picking in self:
            picking.shipment_plan_id = False
            for move in picking.move_lines:
                if move.shipment_plan_id:
                    picking.shipment_plan_id = move.shipment_plan_id
                    continue

    @api.multi
    def _prepare_internal_picking_shipment_plan(self):
        self.ensure_one()
        address_id = self.env.user.company_id.with_context(show_address=True).id
        res = {
            "name": "Shipment Plan for %s" % self.name,
            "plan_type": "internal",
            "from_address_id": address_id,
            "to_address_id": address_id,
            "note": self.note,
            "initial_etd": self.scheduled_date - timedelta(days=1),
            "initial_eta": self.scheduled_date,
            "origin": self.origin,
        }
        return res

    @api.multi
    def action_create_internal_picking_shipment_plan(self):
        shipment_obj = self.env["shipment.plan"]
        for picking in self:
            if picking.picking_type_code != "internal":
                continue
            if any(
                move.shipment_plan_id and move.shipment_plan_id.state != "cancel"
                for move in picking.move_lines
            ):
                raise exceptions.UserError(
                    _("Internal Picking %s has already Shipment Plan.") % picking.name
                )
            vals = picking._prepare_internal_picking_shipment_plan()
            new_shipment_plan = shipment_obj.create(vals)
            picking.move_lines.write({"shipment_plan_id": new_shipment_plan.id})

    @api.multi
    def action_view_shipment_plan(self):
        self.ensure_one()
        action = self.env.ref("shipment_plan.action_shipment_plan").read()[0]
        action["domain"] = [("id", "=", self.shipment_plan_id.id)]
        return action

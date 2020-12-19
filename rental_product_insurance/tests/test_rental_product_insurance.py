# Part of rental-vertical See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo.addons.rental_base.tests.stock_common import RentalStockCommon
from odoo import fields


class TestRentalProductInsurance(RentalStockCommon):
    def setUp(self):
        super().setUp()

        self.analytic_account = self.env["account.analytic.account"].create(
            {
                "name": "Analytic Account A",
                "code": "100000",
            }
        )

        # Product Created A
        ProductObj = self.env["product.product"]
        self.productA = ProductObj.create(
            {
                "name": "Product A",
                "type": "product",
                "income_analytic_account_id": self.analytic_account.id,
            }
        )
        # Rental Service (Day) of Product A
        self.rental_service_day = self._create_rental_service_day(self.productA)
        self.product_insurance = self.env.ref(
            "rental_product_insurance.product_product_insurance"
        )
        self.date_start = fields.Date.from_string(fields.Date.today())
        self.date_end = self.date_start + relativedelta(days=1)
        self.rental_order = self.env["sale.order"].create(
            {
                "partner_id": self.partnerA.id,
            }
        )
        self.rental_order_line = self.env["sale.order.line"].new(
            {
                "product_id": self.rental_service_day.id,
                "name": self.rental_service_day.name,
                "rental_type": "new_rental",
                "rental_qty": 2.0,
                "price_unit": 100,
                "product_uom": self.rental_service_day.uom_id.id,
                "start_date": self.date_start,
                "end_date": self.date_end,
                "product_uom_qty": 4.0,
                "rental": True,
            }
        )
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partnerA.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.productA.id,
                            "name": self.productA.name,
                            "price_unit": 100,
                            "product_uom": self.uom_unit.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )

    def test_00_rental_product_insurance_type_product(self):
        self.productA.write(
            {
                "insurance_type": "product",
                "insurance_percent": 20,
                "standard_price": 1000,
            }
        )
        self.rental_service_day.income_analytic_account_id = self.analytic_account
        # test onchange_insurance_product_id
        self.rental_order_line.onchange_insurance_product_id()
        self.rental_order_line.onchange_insurance_amount()
        self.assertEqual(self.rental_order_line.insurance_type, "product")
        self.assertEqual(self.rental_order_line.insurance_percent, 20)
        vals = self.rental_order_line._convert_to_write(self.rental_order_line._cache)
        vals["order_id"] = self.rental_order.id
        self.rental_order_line = self.env["sale.order.line"].create(vals)
        # self.assertEqual(self.rental_order_line.insurance_amount, 200)
        self.assertEqual(self.rental_order_line.insurance_price_unit, 100)
        self.assertEqual(len(self.rental_order.order_line), 2)
        check_insurance = False
        for line in self.rental_order.order_line:
            if line.product_id == self.product_insurance:
                self.insurance_line = line
                self.assertEqual(line.price_unit, 100)
                self.assertEqual(line.product_uom_qty, 2)
                self.assertEqual(
                    line.insurance_origin_line_id.id, self.rental_order_line.id
                )
                self.assertEqual(line.name, "Insurance: Rental of Product A (Day)")
                invoice_line_vals = line._prepare_invoice_line(1)
                self.assertEqual(
                    invoice_line_vals["account_analytic_id"], self.analytic_account.id
                )
                check_insurance = True
        self.assertEqual(check_insurance, True)
        self.rental_order_line.write(
            {
                "insurance_percent": 10,
            }
        )
        self.rental_order_line.onchange_insurance_params()
        self.rental_order_line.onchange_insurance_amount()
        self.assertEqual(self.rental_order_line.update_insurance_line, True)
        self.rental_order_line.update_rental_insurance_line()
        self.assertEqual(self.rental_order_line.insurance_percent, 10)
        # self.assertEqual(self.rental_order_line.insurance_amount, 100)
        self.assertEqual(self.rental_order_line.insurance_price_unit, 50)
        self.assertEqual(self.rental_order_line.product_uom_qty, 4)
        self.assertEqual(self.rental_order_line.update_insurance_line, False)
        self.assertEqual(self.insurance_line.product_uom_qty, 2)
        self.assertEqual(self.insurance_line.price_unit, 50)

        # test onchange_insurance_product_id again in normal sale order
        self.sale_order.order_line.onchange_insurance_product_id()
        self.assertEqual(self.sale_order.order_line.insurance_type, "product")
        self.assertEqual(self.sale_order.order_line.insurance_percent, 20)

    def test_01_rental_product_insurance_type_rental(self):
        self.productA.write(
            {
                "insurance_type": "rental",
                "insurance_percent": 20,
                "standard_price": 1000,
            }
        )
        # test onchange_insurance_product_id
        self.rental_order_line.onchange_insurance_product_id()
        self.assertEqual(self.rental_order_line.insurance_type, "rental")

        self.assertEqual(self.rental_order_line.insurance_percent, 20)
        self.rental_order_line.insurance_percent = 10
        self.rental_order_line.onchange_insurance_amount()
        vals = self.rental_order_line._convert_to_write(self.rental_order_line._cache)
        vals["order_id"] = self.rental_order.id

        self.rental_order_line = self.env["sale.order.line"].create(vals)
        # self.assertEqual(self.rental_order_line.insurance_amount, 40)
        self.assertEqual(self.rental_order_line.insurance_price_unit, 20)
        self.assertEqual(len(self.rental_order.order_line), 2)
        check_insurance = False
        for line in self.rental_order.order_line:
            if line.product_id == self.product_insurance:
                self.assertEqual(line.price_unit, 20)
                self.assertEqual(line.product_uom_qty, 2)
                self.assertEqual(
                    line.insurance_origin_line_id.id, self.rental_order_line.id
                )
                self.assertEqual(line.name, "Insurance: Rental of Product A (Day)")
                check_insurance = True
        self.assertEqual(check_insurance, True)

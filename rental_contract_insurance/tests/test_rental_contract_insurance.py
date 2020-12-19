# Part of rental-vertical See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo.addons.rental_base.tests.stock_common import RentalStockCommon
from odoo import fields


class TestRentalContractInsurance(RentalStockCommon):
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
                "insurance_type": "product",
                "insurance_percent": 20,
                "standard_price": 1000,
            }
        )
        self.productA.write(
            {
                "rental": True,
                "rental_of_month": True,
                "rental_of_day": True,
                "rental_price_month": 1000,
                "rental_price_day": 100,
                "income_analytic_account_id": self.analytic_account.id,
            }
        )
        self.today = fields.Date.from_string(fields.Date.today())
        self.date_three_month_later = self.today + relativedelta(months=3)
        self.date_19_later = self.today + relativedelta(days=19)
        self.rental_order = (
            self.env["sale.order"]
            .with_context(
                {
                    "default_type_id": self.rental_sale_type.id,
                }
            )
            .create(
                {
                    "partner_id": self.partnerA.id,
                    "pricelist_id": self.env.ref("product.list0").id,
                }
            )
        )
        self.contract_insurance_product = self.env.ref(
            "rental_contract_insurance.product_product_contract_insurance"
        )
        self.product_insurance = self.env.ref(
            "rental_product_insurance.product_product_insurance"
        )

    def _run_sol_onchange_display_product_id(self, line):
        line.onchange_display_product_id()  # product_id, rental changed
        line.product_id_change()
        line.onchange_rental()  # product_id changed again
        line.product_id_change()  # product_uom changed
        line.product_uom_change()
        line.rental_product_id_change()  # set start end date manually
        line.onchange_insurance_amount()  # set insurance_price_unit

    def _run_sol_onchange_product_uom(self, line, product_uom):
        line.product_uom = product_uom
        line.product_uom_change()
        line.product_id_change()
        line.onchange_start_end_date()
        line.start_date_change()
        line.end_date_change()
        line.rental_qty_number_of_days_change()
        line.product_uom_change()
        line.onchange_insurance_amount()  # set insurance_price_unit

    def test_00_rental_contract_insurance(self):
        # add item from pricelist
        line = (
            self.env["sale.order.line"]
            .with_context(
                {
                    "type_id": self.rental_sale_type.id,
                }
            )
            .new(
                {
                    "display_product_id": self.productA.id,
                    "start_date": self.today,
                    "end_date": self.date_three_month_later,
                }
            )
        )
        self._run_sol_onchange_display_product_id(line)
        self._run_sol_onchange_product_uom(line, self.uom_month)
        line.onchange_insurance_product_id()
        vals = line._convert_to_write(line._cache)
        vals["order_id"] = self.rental_order.id
        line = self.env["sale.order.line"].create(vals)
        self.rental_order.action_confirm()
        self.assertEqual(self.rental_order.contract_count, 1)

        check_insurance_line = False
        for line in self.rental_order.order_line:
            if line.product_id == self.contract_insurance_product:
                self.assertEqual(
                    line.display_product_id, self.contract_insurance_product
                )
                self.assertEqual(line.date_start, self.today)
                self.assertEqual(line.date_end, self.date_three_month_later)
                contract_line = line.contract_id.contract_line_ids[0]
                self.assertEqual(contract_line.date_start, self.today)
                self.assertEqual(contract_line.date_end, self.date_three_month_later)
                self.assertEqual(
                    contract_line.analytic_account_id, self.analytic_account
                )
                invoice_line_vals = line._prepare_invoice_line(1)
                self.assertEqual(
                    invoice_line_vals["account_analytic_id"], self.analytic_account.id
                )
                check_insurance_line = True
        self.assertTrue(check_insurance_line, "No found expected insurance line")

    def test_01_rental_contract_insurance_day(self):
        # add item from pricelist
        line = (
            self.env["sale.order.line"]
            .with_context(
                {
                    "type_id": self.rental_sale_type.id,
                }
            )
            .new(
                {
                    "display_product_id": self.productA.id,
                    "start_date": self.today,
                    "end_date": self.date_19_later,
                }
            )
        )
        self._run_sol_onchange_display_product_id(line)
        line.onchange_insurance_product_id()
        vals = line._convert_to_write(line._cache)
        vals["order_id"] = self.rental_order.id
        order_line = self.env["sale.order.line"].create(vals)
        # Set product_uom_qty and number_of_time_unit
        order_line.product_uom_qty = 10
        order_line.number_of_time_unit = 20
        order_line.onchange_insurance_amount()  # reset insurance_price_unit
        order_line.update_rental_insurance_line()
        self.assertEqual(order_line.insurance_price_unit, 10)
        # self.assertEqual(order_line.insurance_amount, 200)
        check_insurance = False
        for line in self.rental_order.order_line:
            if line.product_id == self.product_insurance:
                self.assertEqual(line.price_unit, 10)
                self.assertEqual(line.product_uom_qty, 20)
                check_insurance = True
        self.assertEqual(check_insurance, True)

        order_line.insurance_entire_time = False
        order_line.onchange_insurance_amount()  # reset insurance_price_unit
        self.assertEqual(order_line.insurance_price_unit, 20)
        # self.assertEqual(order_line.insurance_amount, 200)
        order_line.update_rental_insurance_line()
        check_insurance = False
        for line in self.rental_order.order_line:
            if line.product_id == self.product_insurance:
                self.assertEqual(line.price_unit, 20)
                self.assertEqual(line.product_uom_qty, 10)
                check_insurance = True
        self.assertEqual(check_insurance, True)

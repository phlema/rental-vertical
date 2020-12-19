# Part of rental-vertical See LICENSE file for full copyright and licensing details.

{
    "name": "Rental Base",
    "summary": "Base module for rental use cases",
    "description": """Base Module for Rental Support

This module add some basic configuration options and extensions for rental use cases.

Configuration options:
 - Rental Prices: Rental prices can be configured for hourly, daily or monthly rentals.
 - Rental Off-Days: Off-days can be calculated for daily rentals which are excluded from price calculation.
 - Timeline: Use timeline for order regarding a rental product.
 - Rental Product Pack: Rental orders for product packs will also update the stock of pack components.
 - Product Variant: Configure rental products with extended fields and smartbuttons.
 - Product Instance: Use a product as unique product instance with serial number.
 - Product Set: Rental products can be grouped in a set for usage in rental orders.
 - Contract: Rental contracts are automatically created from monthly rentals for periodic invoicing.
 - Repair Order: Support repair orders for product instances.
""",
    "usage": """
Go to Rentals > Configuration > Settings.
Activate the checkboxes for rental extensions.

Please activate the checkbox for using 'Product Variants' in Sales > Configuration > Settings, too.
Otherwise you can not deal with rental orders.
""",
    "version": "12.0.1.0.1",
    "category": "Rental",
    "author": "Odoo Community Association (OCA)/Elego Software Solutions GmbH",
    "depends": [
        "account",
        "board",
        "product_analytic",
        "product_dimension",
        "purchase",
        "sale",
        "sale_order_type",
        "rental_sale",
        "sale_start_end_dates",
        "sale_stock",
        "repair",
        "sales_team",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "data/order_type_data.xml",
        "data/product_uom_data.xml",
        "wizard/update_sale_line_date_view.xml",
        "views/res_config_settings_view.xml",
        "views/stock_picking_views.xml",
        "views/menu_view.xml",
        "views/sale_view.xml",
    ],
    "demo": [],
    "qweb": [],
    "application": True,
    "license": "AGPL-3",
}

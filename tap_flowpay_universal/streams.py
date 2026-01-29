"""Stream type classes for tap-flowpay-universal."""
from singer_sdk import typing as th

from tap_flowpay_universal.client import FlowpayUniversalStream


class OrdersStream(FlowpayUniversalStream):
    """Define custom stream."""

    name = "orders"
    primary_keys = ["id", "updatedAt"]
    replication_key = "updatedAt"

    @property
    def path(self):
        return self.config.get("orders_path")
    
    schema = th.PropertiesList(
        th.Property("id",th.StringType),
        th.Property("createdAt",th.DateTimeType),
        th.Property("updatedAt",th.DateTimeType),
        th.Property("status",th.StringType),
        th.Property("delivery",th.StringType),
        th.Property("payment",th.StringType),
        th.Property("customerId",th.StringType),
        th.Property("customerName",th.StringType),
        th.Property("currency",th.StringType),
        th.Property("totalPrice",th.NumberType),
        th.Property("totalDiscount",th.NumberType),
        th.Property("totalShipping",th.NumberType),
        th.Property("totalTax",th.NumberType),
        th.Property("items", th.ArrayType(th.ObjectType(
            th.Property("productId",th.StringType),
            th.Property("productName",th.StringType),
            th.Property("quantity",th.NumberType),
            th.Property("unitPrice",th.NumberType),
            th.Property("totalPrice",th.NumberType),
            th.Property("discountAmount",th.NumberType),
            th.Property("taxAmount",th.NumberType),
        ))),
        th.Property("billingAddress", th.ObjectType(
            th.Property("line1",th.StringType),
            th.Property("line2",th.StringType),
            th.Property("line3",th.StringType),
            th.Property("city",th.StringType),
            th.Property("state",th.StringType),
            th.Property("country",th.StringType),
            th.Property("zip",th.StringType),
        )),
        th.Property("shippingAddress", th.ObjectType(
            th.Property("line1",th.StringType),
            th.Property("line2",th.StringType),
            th.Property("line3",th.StringType),
            th.Property("city",th.StringType),
            th.Property("state",th.StringType),
            th.Property("country",th.StringType),
            th.Property("zip",th.StringType),
        ))
    ).to_dict()
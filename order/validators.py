from collections import defaultdict

from .exceptions import ShipmentUpdateValidationError
from .models import Order, ShipmentUpdate


class ShipmentUpdatesValidator:
    """
    Validates shipment updates against order line items

    """

    def __init__(self, order: Order):
        """
        Args:
            order (Order): order against which shipment updates are validated
        """
        self.order = order

    def validate(self, shipment_updates: list[ShipmentUpdate]):
        """
        Args:
            shipment_updates (list[ShipmentUpdate]): Shipment updates to validate
        """
        # Sum of quantity shipped in all updates per SKU
        incoming_quantity_shipped_per_sku: dict[str, int] = defaultdict(int)

        for shipment_update in shipment_updates:
            for sku in shipment_update.skus:
                self._validate_sku(sku)

                incoming_quantity_shipped_per_sku[sku] += 1

        self._validate_incoming_quantity_shipped(incoming_quantity_shipped_per_sku)

    def _validate_sku(self, sku: str):
        """
        Args:
            sku (str): SKU to validate

        Raises:
            ShipmentUpdateValidationError: if SKU is not present in order line items or it was already fully shipped
        """
        if sku not in self.order.line_items:
            raise ShipmentUpdateValidationError(
                f"SKU '{sku}' is not present in order line items"
            )

        if self.order.line_items[sku].is_fully_shipped:
            raise ShipmentUpdateValidationError(
                f"Order line item '{sku}' has already been fully shipped"
            )

    def _validate_incoming_quantity_shipped(
        self, incoming_quantity_shipped_per_sku: dict[str, int]
    ):
        """
        Args:
            incoming_quantity_shipped_per_sku (dict[str, int]): sum of quantity shipped in all updates per SKU

        Raises:
            ShipmentUpdateValidationError: If incoming quantity exceeds order line item quantity pending shipment
        """
        for sku, incoming_quantity_shipped in incoming_quantity_shipped_per_sku.items():
            if (
                incoming_quantity_shipped
                > self.order.line_items[sku].quantity_pending_to_ship
            ):
                raise ShipmentUpdateValidationError(
                    f"Shipped quantity for SKU '{sku}' exceeds order line item pending shipment quantity"
                )

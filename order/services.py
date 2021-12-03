from .models import Order, ShipmentUpdate
from .validators import ShipmentUpdatesValidator


class OrderService:
    """
    Order processing service
    """

    @staticmethod
    def add_shipments(order: Order, shipment_updates: list[ShipmentUpdate]):
        """
        Validates shipment update and applies it to order line items, updating quantity shipped and tracking codes

        Args:
            order (Order): order that
            shipment_updates (list[ShipmentUpdate]): Shipment updates payload
        """
        # raises an exception if updates are invalid
        ShipmentUpdatesValidator(order).validate(shipment_updates)

        order.accepted_shipment_updates.append(shipment_updates)

        for shipment_update in shipment_updates:
            for sku in shipment_update.skus:
                order.line_items[sku].tracking_codes.add(shipment_update.tracking_code)
                order.line_items[sku].quantity_shipped += 1

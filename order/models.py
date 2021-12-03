from dataclasses import dataclass, field


@dataclass
class LineItemInfo:
    """
    Contains information about order line items
    """

    quantity: int
    quantity_shipped: int = 0
    tracking_codes: set[str] = field(default_factory=set)

    @property
    def is_fully_shipped(self) -> bool:
        """
        Returns:
            bool: True if given line item has been fully shipped
        """
        return self.quantity == self.quantity_shipped

    @property
    def quantity_pending_to_ship(self) -> int:
        """
        Returns:
            int: Quantity pending shipment
        """
        return self.quantity - self.quantity_shipped


@dataclass
class ShipmentUpdate:
    """
    Contains order shipment update information
    """

    # Each SKU in an update designates a single quantity shipped, repeated SKUs designate greater quantity
    skus: list[str]
    tracking_code: str


@dataclass
class Order:
    """
    Consists of order line items and accepted shipment updates

    Line items info is grouped by SKU, example:
        {
            "SKU1": LineItemInfo(quantity=2),
            "SKU2": LineItemInfo(quantity=1)
        }

    """

    line_items: dict[str, LineItemInfo]
    accepted_shipment_updates: list[list[ShipmentUpdate]] = field(default_factory=list)

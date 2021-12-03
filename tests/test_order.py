import pytest

from order.exceptions import ShipmentUpdateValidationError
from order.models import LineItemInfo, Order, ShipmentUpdate
from order.services import OrderService

SKU_1 = "SKU1"
SKU_2 = "SKU2"
INVALID_SKU = "INVALID"
TRACKING_CODE_1 = "1234"
TRACKING_CODE_2 = "5678"


@pytest.fixture
def order():
    return Order(line_items={SKU_1: LineItemInfo(quantity=2), SKU_2: LineItemInfo(quantity=2)})


@pytest.mark.parametrize(
    "shipment_updates,expected_tracking_codes",
    (
        # Single part and one tracking code
        (
            [ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_1, SKU_2, SKU_2])],
            {TRACKING_CODE_1},
        ),
        # Multipart and one tracking code
        (
            [
                ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1]),
                ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_2]),
                ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_2]),
            ],
            {TRACKING_CODE_1},
        ),
        # Multipart and multiple tracking codes
        (
            [
                ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1]),
                ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_2]),
                ShipmentUpdate(tracking_code=TRACKING_CODE_2, skus=[SKU_1, SKU_2]),
            ],
            {TRACKING_CODE_1, TRACKING_CODE_2},
        ),
    ),
    ids=[
        "single_part",
        "multipart-one_tracking_code",
        "multipart-multiple_tracking_codes",
    ],
)
def test_order_add_shipments_success_all_shipped(shipment_updates, expected_tracking_codes, order):
    OrderService.add_shipments(order, shipment_updates)

    for line_item_info in order.line_items.values():
        assert line_item_info.is_fully_shipped is True, line_item_info
        assert line_item_info.tracking_codes == expected_tracking_codes

    assert shipment_updates in order.accepted_shipment_updates


@pytest.mark.parametrize(
    "shipment_updates",
    (
        # Single part
        [ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_2, INVALID_SKU])],
        [
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_2]),
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[INVALID_SKU]),
        ],
    ),
    ids=["single_part", "multipart"],
)
def test_order_add_shipments_fail_sku_not_present_in_line_items(shipment_updates, order):
    with pytest.raises(ShipmentUpdateValidationError) as excinfo:
        OrderService.add_shipments(order, shipment_updates)

    assert f"SKU '{INVALID_SKU}' is not present in order line items" in str(excinfo)
    assert shipment_updates not in order.accepted_shipment_updates


@pytest.mark.parametrize(
    "shipment_updates",
    (
        # Single part
        [ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_1, SKU_2, SKU_2, SKU_2])],
        # Multipart
        [
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_1, SKU_2]),
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_2, SKU_2]),
        ],
    ),
    ids=["single_part", "multipart"],
)
def test_order_add_shipments_fail_quantity_exceeded(shipment_updates, order):
    with pytest.raises(ShipmentUpdateValidationError) as excinfo:
        OrderService.add_shipments(order, shipment_updates)

    assert f"Shipped quantity for SKU '{SKU_2}' exceeds order line item pending shipment quantity" in str(excinfo)
    assert shipment_updates not in order.accepted_shipment_updates


@pytest.mark.parametrize(
    "shipment_updates",
    (
        # Single part
        [ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_1, SKU_2])],
        # Multipart
        [
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1, SKU_2]),
            ShipmentUpdate(tracking_code=TRACKING_CODE_1, skus=[SKU_1]),
        ],
    ),
    ids=["single_part", "multipart"],
)
def test_order_add_shipments_fail_already_shipped(shipment_updates, order):
    OrderService.add_shipments(order, shipment_updates)
    expected_accepted_shipment_updates = order.accepted_shipment_updates

    assert shipment_updates in expected_accepted_shipment_updates

    with pytest.raises(ShipmentUpdateValidationError) as excinfo:
        OrderService.add_shipments(order, shipment_updates)

    assert f"Order line item '{SKU_1}' has already been fully shipped" in str(excinfo)
    assert order.accepted_shipment_updates == expected_accepted_shipment_updates

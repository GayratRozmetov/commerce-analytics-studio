import pandas as pd
import pytest

from analytics import calculate_metrics, prepare_data


def test_prepare_data_and_metrics():
    frame = pd.DataFrame(
        [{"order_date": "2026-01-01", "order_id": "A-1", "customer": "Demo", "country": "TR", "product": "Tee", "category": "Tops", "quantity": 2, "unit_price": 50, "stock": 10}]
    )
    data = prepare_data(frame)
    metrics = calculate_metrics(data)
    assert data.iloc[0]["revenue"] == 100
    assert metrics.orders == 1
    assert metrics.average_order_value == 100


def test_missing_columns_are_reported():
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_data(pd.DataFrame({"order_id": [1]}))

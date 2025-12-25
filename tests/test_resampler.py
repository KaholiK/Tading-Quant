from trading_system.data.resampler import resample


def test_resample_passthrough():
    data = [{"a": 1}, {"a": 2}]
    assert resample(data) == data

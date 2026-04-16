"""Signal validation helpers for distribution bot."""


def is_valid_signal(signal) -> bool:
    return bool(
        signal
        and getattr(signal, "pair", None)
        and getattr(signal, "direction", None)
        and getattr(signal, "entry_price", None) is not None
        and getattr(signal, "confidence", 0) >= 0
    )

from decimal import Decimal, getcontext
import math

# 🔥 Set high precision
getcontext().prec = 28

class MarketCalculator:

    DIG1 = Decimal("55")
    DIG2 = Decimal("107")
    DIG3 = Decimal("180")
    BASE = Decimal("180")

    @classmethod
    def calculate(cls, open_price: float):

        open_price = Decimal(str(open_price))

        # sqrt using Decimal
        square = open_price.sqrt()

        r1_d = (cls.DIG1 * square) / cls.BASE
        r2_d = (cls.DIG2 * square) / cls.BASE
        r3_d = (cls.DIG3 * square) / cls.BASE

        r1_f = open_price + r1_d
        r2_f = open_price + r2_d
        buy  = open_price + r3_d

        s1_f = open_price - r1_d
        s2   = open_price - r2_d
        sell = open_price - r3_d

        # 🔥 Convert to 8 decimal string (no rounding logic)
        return {
            "square": float(square.quantize(Decimal("0.0000000000000"))),
            "base": int(cls.BASE),
            "dig1": int(cls.DIG1),
            "dig2": int(cls.DIG2),
            "dig3": int(cls.DIG3),

            "r1_d": float(r1_d.quantize(Decimal("0.00000000000000"))),
            "r2_d": float(r2_d.quantize(Decimal("0.0000000000000"))),
            "r3_d": float(r3_d.quantize(Decimal("0.0000000000000"))),

            "r1_f": float(r1_f.quantize(Decimal("0.0000000000000"))),
            "r2_f": float(r2_f.quantize(Decimal("0.0000000000000"))),
            "buy":  float(buy.quantize(Decimal("0.0000000000000"))),

            "s1_f": float(s1_f.quantize(Decimal("0.0000000000000"))),
            "s2":   float(s2.quantize(Decimal("0.0000000000000"))),
            "sell": float(sell.quantize(Decimal("0.0000000000000"))),
        }

import unittest

from calculator import CalculatorError, calculate, format_result


class CalculatorTests(unittest.TestCase):
    def test_arithmetic_and_operator_precedence(self):
        self.assertEqual(calculate("2 + 3 × 4"), 14)

    def test_natural_percentage_expression(self):
        self.assertEqual(calculate("15% dari 200"), 30)

    def test_parentheses_and_implicit_multiplication(self):
        self.assertEqual(calculate("2(3 + 4)"), 14)

    def test_division_by_zero_has_clear_error(self):
        with self.assertRaisesRegex(CalculatorError, "membagi dengan nol"):
            calculate("1 / 0")

    def test_rejects_code_execution_and_unsupported_nodes(self):
        with self.assertRaises(CalculatorError):
            calculate("__import__('os').system('echo unsafe')")

    def test_limits_exponent_size(self):
        with self.assertRaisesRegex(CalculatorError, "Pangkat maksimal"):
            calculate("2 ** 13")

    def test_rejects_unreasonably_large_integer_literals(self):
        with self.assertRaisesRegex(CalculatorError, "di luar rentang"):
            calculate("*".join(["9 ** 12"] * 30))

    def test_zero_to_negative_power_has_calculator_error(self):
        with self.assertRaises(CalculatorError):
            calculate("0 ** -1")

    def test_formats_integral_float_without_decimal(self):
        self.assertEqual(format_result(25.0), "25")


if __name__ == "__main__":
    unittest.main()

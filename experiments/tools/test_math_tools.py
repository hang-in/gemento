"""Unit tests for math_tools (stdlib unittest, no external test runner required)."""
import unittest

from math_tools import calculator, solve_linear_system, linprog


class TestCalculator(unittest.TestCase):
    def test_basic_order_of_ops(self):
        self.assertAlmostEqual(calculator("2+3*4"), 14.0)

    def test_parentheses_and_power(self):
        self.assertAlmostEqual(calculator("(10-4)**2"), 36.0)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            calculator("1/0")

    def test_unsafe_expression_blocked(self):
        with self.assertRaises((ValueError, SyntaxError)):
            calculator("__import__('os')")

    def test_call_node_blocked(self):
        with self.assertRaises(ValueError):
            calculator("abs(-1)")

    def test_bitxor_hint_message(self):
        """BitXor 에러는 '**' 사용 힌트를 포함해야 한다."""
        with self.assertRaises(ValueError) as ctx:
            calculator("2^10")
        msg = str(ctx.exception)
        self.assertIn("BitXor", msg)
        self.assertIn("**", msg)
        self.assertIn("XOR", msg)


class TestSolveLinearSystem(unittest.TestCase):
    def test_2x2_system(self):
        x = solve_linear_system([[2, 1], [1, 3]], [5, 10])
        self.assertAlmostEqual(x[0], 1.0, places=9)
        self.assertAlmostEqual(x[1], 3.0, places=9)

    def test_singular_matrix_raises(self):
        with self.assertRaises(ValueError):
            solve_linear_system([[1, 2], [2, 4]], [3, 6])


class TestLinprog(unittest.TestCase):
    def test_math04_lp(self):
        # Maximize 50x + 40y + 30z subject to:
        # 2x+3y+4z <= 240, 3x+2y+z <= 150, x>=10, y>=10, z>=10
        # Actual optimal: x=31, y=10, z=37, profit=3060
        r = linprog(
            c=[-50, -40, -30],
            A_ub=[[2, 3, 4], [3, 2, 1]],
            b_ub=[240, 150],
            bounds=[[10, None], [10, None], [10, None]],
        )
        self.assertTrue(r["success"], r)
        x = r["x"]
        self.assertAlmostEqual(x[0], 31.0, places=4)
        self.assertAlmostEqual(x[1], 10.0, places=4)
        self.assertAlmostEqual(x[2], 37.0, places=4)
        self.assertAlmostEqual(r["fun"], -3060.0, places=3)


if __name__ == "__main__":
    unittest.main()

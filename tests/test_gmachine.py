import unittest

from cnc.gcode import *
from cnc.gmachine import *
from cnc.coordinates import *
from cnc.heater import *
from cnc.pid import *
from cnc.config import *


class TestGMachine(unittest.TestCase):
    def setUp(self):
        Pid.FIX_TIME_S = 0.01
        Heater.LOOP_INTERVAL_S = 0.001
        hal.gimbal.set_position(0, 0)

    def tearDown(self):
        pass

    def test_reset(self):
        # reset() resets all configurable from gcode things.
        m = GMachine()
        m.do_command(GCode.parse_line("G20"))
        m.do_command(GCode.parse_line("G91"))
        m.do_command(GCode.parse_line("X1 Y1 Z1"))
        m.reset()
        m.do_command(GCode.parse_line("X3 Y4 Z5 E6"))
        self.assertEqual(m.position(), Coordinates(3, 4, 5, 6))

    def test_safe_zero(self):
        m = GMachine()
        m.do_command(GCode.parse_line("X1 Y2 Z3 E4"))
        m.safe_zero()
        self.assertEqual(m.position(), Coordinates(0, 0, 0, 4))

    def test_none(self):
        # GMachine must ignore None commands, since GCode.parse_line()
        # returns None if no gcode found in line.
        m = GMachine()
        m.do_command(None)
        self.assertEqual(m.position(), Coordinates(0, 0, 0, 0))

    def test_unknown(self):
        # Test commands which doesn't exists
        m = GMachine()
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G99699 X1 Y2 Z3"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("M99699"))

    # Test gcode commands.
    def test_g0_g1(self):
        m = GMachine()
        m.do_command(GCode.parse_line("G0 X10 Y10 Z11 A20 B-50"))
        self.assertEqual(m.position(), Coordinates(10, 10, 11, 0))
        self.assertEqual(m.angular_position(), [20, -50])
        m.do_command(GCode.parse_line("G0 X3 Y2 Z1 E2"))
        self.assertEqual(m.position(), Coordinates(3, 2, 1, 2))
        m.do_command(GCode.parse_line("G1 X1 Y2 Z3 E4"))
        self.assertEqual(m.position(), Coordinates(1, 2, 3, 4))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 F-1"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 X-1 Y0 Z0"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 X0 Y-1 Z0"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 X0 Y0 Z-1"))

    def test_feed_rate(self):
        PulseGenerator.AUTO_VELOCITY_ADJUSTMENT = False
        m = GMachine()
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 X1 F-1"))
        cl = "G1 X1 F" + str(MIN_VELOCITY_MM_PER_MIN - 0.0000001)
        self.assertRaises(GMachineException, m.do_command,
                          GCode.parse_line(cl))
        m.do_command(GCode.parse_line("G1 X100 F"
                                      + str(MAX_VELOCITY_MM_PER_MIN_X)))
        m.do_command(GCode.parse_line("G1 Y100 F"
                                      + str(MAX_VELOCITY_MM_PER_MIN_Y)))
        m.do_command(GCode.parse_line("G1 Z100 F"
                                      + str(MAX_VELOCITY_MM_PER_MIN_Z)))
        m.do_command(GCode.parse_line("G1 E100 F"
                                      + str(m._get_extruder_max_speed())))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G1 X0 F999999"))
        s = "G1 X0 F" + str(MAX_VELOCITY_MM_PER_MIN_X + 1)
        self.assertRaises(GMachineException, m.do_command, GCode.parse_line(s))
        s = "G1 Y0 F" + str(MAX_VELOCITY_MM_PER_MIN_Y + 1)
        self.assertRaises(GMachineException, m.do_command, GCode.parse_line(s))
        s = "G1 Z0 F" + str(MAX_VELOCITY_MM_PER_MIN_Z + 1)
        self.assertRaises(GMachineException, m.do_command, GCode.parse_line(s))
        s = "G1 E0 F" + str(m._get_extruder_max_speed() + 1)
        self.assertRaises(GMachineException, m.do_command, GCode.parse_line(s))
        PulseGenerator.AUTO_VELOCITY_ADJUSTMENT = True
        m.do_command(GCode.parse_line("G1 X10 Y10 Z10 F9999999999999999999"))
        m.do_command(GCode.parse_line("G2 I0.1 F9999999999999999999"))
        m.do_command(GCode.parse_line("G2 I10 F9999999999999999999"))
        PulseGenerator.AUTO_VELOCITY_ADJUSTMENT = AUTO_VELOCITY_ADJUSTMENT

    def test_g2_g3(self):
        m = GMachine()

        # Tests for invalid feed rate
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 I1 J1 F-1"))

        # Tests for invalid radii on all planes
        m.do_command(GCode.parse_line("G19"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 I1 J0 K0"))
        m.do_command(GCode.parse_line("G18"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 I0 J1 K0"))
        m.do_command(GCode.parse_line("G17"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 I0 J0 K1"))

        # Tests for invalid end point
        self.assertRaises(GMachineException, m.do_command,
                          GCode.parse_line("G2 X99999999 Y99999999 I49999999.5 J49999999.5"))
        self.assertRaises(GMachineException,
                          m.do_command,
                          GCode.parse_line("G2 X2 Y2 Z99999999 I1 J1"))
        self.assertEqual(m.position(), Coordinates(0, 0, 0, 0))

        # Tests both start and end points are bounded but the circle is not
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G2 X4 Y4 I2 J2"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 X4 Y4 I2 J2"))

        # Tests that a full circle can be drawn both clockwise and counterclockwise
        m.do_command(GCode.parse_line("G17"))
        m.do_command(GCode.parse_line("G1 X1"))
        m.do_command(GCode.parse_line("G2 J1"))
        m.do_command(GCode.parse_line("G3 J1"))
        self.assertEqual(m.position(), Coordinates(1, 0, 0, 0))

        # Tests that each arc is properly considered and included
        # Q1
        m.do_command(GCode.parse_line("G1 X0 Y1"))
        m.do_command(GCode.parse_line("G2 X1 Y0 J-1"))
        m.do_command(GCode.parse_line("G3 X0 Y1 I-1"))
        # Q2
        m.do_command(GCode.parse_line("G1 X{} Y0".format(TABLE_SIZE_X_MM - 1)))
        m.do_command(GCode.parse_line("G2 X{} Y1 I1".format(TABLE_SIZE_X_MM)))
        m.do_command(GCode.parse_line("G3 X{} Y0 J-1".format(TABLE_SIZE_X_MM - 1)))
        # Q3
        m.do_command(GCode.parse_line("G1 X{} Y{}".format(TABLE_SIZE_X_MM, TABLE_SIZE_Y_MM - 1)))
        m.do_command(GCode.parse_line("G2 X{} Y{} J1".format(TABLE_SIZE_X_MM - 1, TABLE_SIZE_Y_MM)))
        m.do_command(GCode.parse_line("G3 X{} Y{} I1".format(TABLE_SIZE_X_MM, TABLE_SIZE_Y_MM - 1)))
        # Q4
        m.do_command(GCode.parse_line("G1 X1 Y{}".format(TABLE_SIZE_Y_MM)))
        m.do_command(GCode.parse_line("G2 X0 Y{} I-1".format(TABLE_SIZE_Y_MM - 1)))
        m.do_command(GCode.parse_line("G3 X1 Y{} J1".format(TABLE_SIZE_Y_MM)))

        # Tests that end points not on the defined circle raise an exception
        m.do_command(GCode.parse_line("G1 X0 Y0"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G3 X4 Y2 J2"))
        m.do_command(GCode.parse_line("G1 X1 Y1"))
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G2 X2 I-1"))

    def test_g4(self):
        m = GMachine()
        st = time.time()
        m.do_command(GCode.parse_line("G4 P0.5"))
        self.assertLess(0.5, time.time() - st)
        self.assertRaises(GMachineException,
                          m.do_command, GCode.parse_line("G4 P-0.5"))

    def test_g17_g18_g19(self):
        m = GMachine()
        m.do_command(GCode.parse_line("G19"))
        self.assertEqual(m.plane(), PLANE_YZ)
        m.do_command(GCode.parse_line("G18"))
        self.assertEqual(m.plane(), PLANE_ZX)
        m.do_command(GCode.parse_line("G17"))
        self.assertEqual(m.plane(), PLANE_XY)

    def test_g20_g21(self):
        m = GMachine()
        m.do_command(GCode.parse_line("G20"))
        m.do_command(GCode.parse_line("X3 Y2 Z1 E0.5"))
        self.assertEqual(m.position(), Coordinates(76.2, 50.8, 25.4, 12.7))
        m.do_command(GCode.parse_line("G21"))
        m.do_command(GCode.parse_line("X3 Y2 Z1 E0.5"))
        self.assertEqual(m.position(), Coordinates(3, 2, 1, 0.5))

    def test_g90_g91(self):
        m = GMachine()
        m.do_command(GCode.parse_line("G91"))
        m.do_command(GCode.parse_line("X1 Y1 Z1 E1 A1"))
        m.do_command(GCode.parse_line("X1 Y1 Z1 A1"))
        m.do_command(GCode.parse_line("X1 Y1"))
        m.do_command(GCode.parse_line("X1"))
        self.assertEqual(m.position(), Coordinates(4, 3, 2, 1))
        self.assertEqual(m.angular_position(), [2, 0])
        m.do_command(GCode.parse_line("X-1 Y-1 Z-1 E-1"))
        m.do_command(GCode.parse_line("G90"))
        m.do_command(GCode.parse_line("X1 Y1 Z1 E1 A1"))
        self.assertEqual(m.position(), Coordinates(1, 1, 1, 1))
        self.assertEqual(m.angular_position(), [1, 0])

if __name__ == '__main__':
    unittest.main()

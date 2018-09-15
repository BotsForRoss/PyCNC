from __future__ import division

import cnc.logging_config as logging_config
from cnc import hal
from cnc.pulses import *
from cnc.coordinates import *
from cnc.heater import *
from cnc.enums import *
from cnc.watchdog import *
from cnc.audio import AudioPlayer


class GMachineException(Exception):
    """ Exceptions while processing gcode line.
    """
    pass


class GMachine(object):
    """ Main object which control and keep state of whole machine: steppers,
        spindle, extruder etc
    """

    def __init__(self):
        """ Initialization.
        """
        self._position = Coordinates(0.0, 0.0, 0.0, 0.0)
        # init variables
        self._velocity = 0
        self._local = None
        self._convertCoordinates = 0
        self._absoluteCoordinates = 0
        self._plane = None
        self._extruder_id = 0
        hal.init()
        self.watchdog = HardwareWatchdog()

        self.reset()

    def release(self):
        """ Free all resources.
        """
        AudioPlayer.stop()
        hal.deinit()

    def reset(self):
        """ Reinitialize all program configurable thing.
        """
        self._velocity = min(MAX_VELOCITY_MM_PER_MIN_X,
                             MAX_VELOCITY_MM_PER_MIN_Y,
                             MAX_VELOCITY_MM_PER_MIN_Z,
                             self._get_extruder_max_speed())
        self._local = Coordinates(0.0, 0.0, 0.0, 0.0)
        self._convertCoordinates = 1.0
        self._absoluteCoordinates = True
        self._plane = PLANE_XY

    def __check_delta(self, delta):
        pos = self._position + delta
        if not pos.is_in_aabb(Coordinates(0.0, 0.0, 0.0, 0.0),
                Coordinates(TABLE_SIZE_X_MM, TABLE_SIZE_Y_MM, TABLE_SIZE_Z_MM, 0)) or \
                pos.e < 0 or pos.e > EXTRUDER_LENGTH_MM:
            raise GMachineException("out of effective area")

    # noinspection PyMethodMayBeStatic
    def __check_velocity(self, max_velocity):
        if max_velocity.x > MAX_VELOCITY_MM_PER_MIN_X \
                or max_velocity.y > MAX_VELOCITY_MM_PER_MIN_Y \
                or max_velocity.z > MAX_VELOCITY_MM_PER_MIN_Z \
                or max_velocity.e > self._get_extruder_max_speed():
            raise GMachineException("out of maximum speed")

    def _get_extruder(self):
        """
        Returns:
            Extruder -- the current extruder
        """

        return hal.get_extruder(self._extruder_id)

    def _get_extruder_max_speed(self):
        """
        Returns:
            float -- the max speed of the current extruder in mm/min
        """

        return self._get_extruder().get_max_speed() * 60.0

    def _get_extruder_speed(self, delta_mm, velocity_mm_per_min):
        """
        Pull the E axis speed out of the delta position vector and overall speed about all axes.
        This is also done in pulses.py, but must be repeated because extruders don't use pulses.

        Arguments:
            delta_mm {Coordinates} -- the difference in position in mm
            velocity_mm_per_min {float} -- the speed about all axes in mm/min

        Returns:
            {float} -- the speed of the E axis only
        """
        distance_mm = abs(delta_mm)
        distance_total_mm = distance_mm.length()
        if distance_total_mm == 0:
            return 0
        velocity = distance_mm * (velocity_mm_per_min / distance_total_mm)
        return velocity.e

    def _move_linear(self, delta, velocity):
        delta = delta.round(1.0 / STEPPER_PULSES_PER_MM_X,
                            1.0 / STEPPER_PULSES_PER_MM_Y,
                            1.0 / STEPPER_PULSES_PER_MM_Z,
                            1.0 / STEPPER_PULSES_PER_MM_E)
        if delta.is_zero():
            return
        self.__check_delta(delta)

        logging.info("Moving linearly {}".format(delta))
        gen = PulseGeneratorLinear(delta, velocity)
        self.__check_velocity(gen.max_velocity())

        extruder_speed = self._get_extruder_speed(delta, velocity)
        self._start_extruder_move(delta.e, extruder_speed)
        hal.move(gen)

        # save position
        self._position = self._position + delta

    @staticmethod
    def __quarter(a, b):
        """Takes the coordinates a and b of a point relative to the center of the circle
            and returns the quarter of the circle the point is in
        
        Arguments:
            a {float} -- The first coordinate
            b {float} -- The second coordinate
        
        Returns:
            {int} -- The quarter the specified point exists in
        """

        if a > 0 and b >= 0:
            return 1
        if a <= 0 and b > 0:
            return 2
        if a < 0 and b <= 0:
            return 3
        if a >= 0 and b < 0:
            return 4

    def __check_circle(self, delta_a, delta_b, radius_a, radius_b, direction, position_a, position_b, table_a, table_b):
        """Validates the circle to be drawn, checking for a valid radius, a valid endpoint, and if the circle 
            is bounded within the table

            The coordinates are labeled as a and b because the plane is selectable and a and b stand for arbitrary 
            combinations of x, y and z.
        
        Arguments:
            delta_a, delta_b {float} -- coordinates of the endpoint relative to the position
            radius_a, radius_b {float} -- coordinates of the circle's center relative to the position
            direction {RotationalDirection(Enum)} -- the direction the circle will draw
            position_a, position_b {float} -- the current position (starting position) in absolute coordinates
            table_a, table_b {int} -- the table's maximum for both the a and b axis
        
        Raises:
            GMachineException -- raised if the radius is zero
            GMachineException -- raised if the endpoint not on the defined circle
            GMachineException -- raised if the circle would draw out of bounds
        """

        radius = math.hypot(radius_a, radius_b)
        if radius == 0:
            raise GMachineException("circle radius is zero")
        # check if (delta_a, delta_b) is on the specified circle
        if math.hypot(delta_a - radius_a, delta_b - radius_b) != radius:
            raise GMachineException("endpoint not on circle")
        # check if the drawn circle is inside the table
        start_quarter = GMachine.__quarter(-radius_a, -radius_b)
        if delta_a == 0 and delta_b == 0: # If the endpoint and position are the same, check the full circle
            end_quarter = 5
        else:
            end_quarter = GMachine.__quarter(delta_a - radius_a, delta_b - radius_b)
        
        if start_quarter == end_quarter:
            return
        
        # If the start and end points are not in the same quarter, there will be new maximum values that have to be checked against
        # boundry conditions
        is_raise = False
        quarter = start_quarter
        prev_quarter = quarter
        for _ in range(4):
            if direction == CW:
                quarter -= 1
                if quarter == 0: quarter = 4
            else:
                quarter += 1
                if quarter == 5: quarter = 1

            if (quarter == 1 and prev_quarter == 4) or (quarter == 4 and prev_quarter == 1):
                is_raise = (position_a + radius_a + radius > table_a)
            elif (quarter == 1 and prev_quarter == 2) or (quarter == 2 and prev_quarter == 1):
                is_raise = (position_b + radius_b + radius > table_b)
            elif (quarter == 2 and prev_quarter == 3) or (quarter == 3 and prev_quarter == 2):
                is_raise = (position_a + radius_a - radius < 0)
            elif (quarter == 3 and prev_quarter == 4) or (quarter == 4 and prev_quarter == 3):
                is_raise = (position_b + radius_b - radius < 0)
            if is_raise:
                raise GMachineException("circle out of bounds")

            if quarter == end_quarter:
                break
            prev_quarter = quarter


    def _move_circular(self, delta, radius, velocity, direction):
        delta = delta.round(1.0 / STEPPER_PULSES_PER_MM_X,
                            1.0 / STEPPER_PULSES_PER_MM_Y,
                            1.0 / STEPPER_PULSES_PER_MM_Z,
                            1.0 / STEPPER_PULSES_PER_MM_E)
        radius = radius.round(1.0 / STEPPER_PULSES_PER_MM_X,
                              1.0 / STEPPER_PULSES_PER_MM_Y,
                              1.0 / STEPPER_PULSES_PER_MM_Z,
                              1.0 / STEPPER_PULSES_PER_MM_E)
        self.__check_delta(delta)
        # get delta vector and put it on circle
        if self._plane == PLANE_XY:
            self.__check_circle(delta.x, delta.y, radius.x, radius.y,
                                direction, self._position.x,
                                self._position.y, TABLE_SIZE_X_MM,
                                TABLE_SIZE_Y_MM)
        elif self._plane == PLANE_YZ:
            self.__check_circle(delta.y, delta.z, radius.y, radius.z,
                                direction, self._position.y,
                                self._position.z, TABLE_SIZE_Y_MM,
                                TABLE_SIZE_Z_MM)
        elif self._plane == PLANE_ZX:
            self.__check_circle(delta.z, delta.x, radius.z, radius.x,
                                direction, self._position.z,
                                self._position.x, TABLE_SIZE_Z_MM,
                                TABLE_SIZE_X_MM)
        logging.info("Moving circularly {} {} {} with radius {}"
                     " and velocity {}".format(self._plane, delta,
                                               direction, radius, velocity))
        gen = PulseGeneratorCircular(delta, radius, self._plane,
                                     direction, velocity)
        self.__check_velocity(gen.max_velocity())
        # do movements
        extruder_speed = self._get_extruder_speed(delta, velocity)
        self._start_extruder_move(delta.e, extruder_speed)
        hal.move(gen)
        # save position
        self._position = self._position + delta

    def safe_zero(self, x=True, y=True, z=True):
        """ Move head to zero position safely.
        :param x: boolean, move X axis to zero
        :param y: boolean, move Y axis to zero
        :param z: boolean, move Z axis to zero
        """
        if x and not y:
            self._move_linear(Coordinates(-self._position.x, 0, 0, 0),
                              MAX_VELOCITY_MM_PER_MIN_X)
        elif y and not x:
            self._move_linear(Coordinates(0, -self._position.y, 0, 0),
                              MAX_VELOCITY_MM_PER_MIN_X)
        elif x and y:
            d = Coordinates(-self._position.x, -self._position.y, 0, 0)
            self._move_linear(d, min(MAX_VELOCITY_MM_PER_MIN_X,
                                     MAX_VELOCITY_MM_PER_MIN_Y))
        if z:
            d = Coordinates(0, 0, -self._position.z, 0)
            self._move_linear(d, MAX_VELOCITY_MM_PER_MIN_Z)

    def position(self):
        """ Return current machine position (after the latest command)
            Note that hal might still be moving motors and in this case
            function will block until motors stops.
            This function for tests only.
            :return current position.
        """
        hal.join()
        return self._position

    def plane(self):
        """ Return current plane for circular interpolation. This function for
            tests only.
            :return current plane.
        """
        return self._plane

    def _start_extruder_move(self, delta, speed):
        """
        Start moving the current extruder asynchronously

        Arguments:
            delta {float} -- the difference in position, in mm
            speed {float} -- the speed to move the extruder, in mm/minute
        """
        extruder = hal.get_extruder(self._extruder_id)
        pos = extruder.get_position()
        extruder.set_position(pos + delta, speed / 60.0)

    def _set_extruder(self, extruder_id):
        """
        Change extruders

        Arguments:
            extruder_id {int} -- the id of the extruder from 0 to NUM_EXTRUDERS
        """
        if extruder_id < 0 or extruder_id >= len(EXTRUDER_CONFIG):
            raise ValueError('invalid extruder id {}'.format(extruder_id))
        extruder = hal.get_extruder(extruder_id)
        self._position.e = extruder.get_position()
        self._extruder_id = extruder_id

    def do_command(self, gcode):
        """ Perform action.
        :param gcode: GCode object which represent one gcode line
        :return String if any answer require, None otherwise.
        """
        if gcode is None:
            return None
        answer = None
        logging.debug("got command " + str(gcode.params))
        # read command
        c = gcode.command()
        if c is None and gcode.has_coordinates():
            c = 'G1'
        # read parameters
        if self._absoluteCoordinates:
            coord = gcode.coordinates(self._position - self._local,
                                      self._convertCoordinates)
            coord = coord + self._local
            delta = coord - self._position
        else:
            delta = gcode.coordinates(Coordinates(0.0, 0.0, 0.0, 0.0),
                                      self._convertCoordinates)
            # coord = self._position + delta
        velocity = gcode.get('F', self._velocity)
        radius = gcode.radius(Coordinates(0.0, 0.0, 0.0, 0.0),
                              self._convertCoordinates)
        # check parameters
        if velocity < MIN_VELOCITY_MM_PER_MIN:
            raise GMachineException("feed speed too low")
        # select command and run it
        if c == 'G0':  # rapid move
            vl = max(MAX_VELOCITY_MM_PER_MIN_X,
                     MAX_VELOCITY_MM_PER_MIN_Y,
                     MAX_VELOCITY_MM_PER_MIN_Z,
                     self._get_extruder_max_speed())
            l = delta.length()
            if l > 0:
                proportion = abs(delta) / l
                if proportion.x > 0:
                    v = int(MAX_VELOCITY_MM_PER_MIN_X / proportion.x)
                    if v < vl:
                        vl = v
                if proportion.y > 0:
                    v = int(MAX_VELOCITY_MM_PER_MIN_Y / proportion.y)
                    if v < vl:
                        vl = v
                if proportion.z > 0:
                    v = int(MAX_VELOCITY_MM_PER_MIN_Z / proportion.z)
                    if v < vl:
                        vl = v
                if proportion.e > 0:
                    v = int(self._get_extruder_max_speed() / proportion.e)
                    if v < vl:
                        vl = v
            self._move_linear(delta, vl)
        elif c == 'G1':  # linear interpolation
            self._move_linear(delta, velocity)
        elif c == 'G2':  # circular interpolation, clockwise
            self._move_circular(delta, radius, velocity, CW)
        elif c == 'G3':  # circular interpolation, counterclockwise
            self._move_circular(delta, radius, velocity, CCW)
        elif c == 'G4':  # delay in s
            if not gcode.has('P'):
                raise GMachineException("P is not specified")
            pause = gcode.get('P', 0)
            if pause < 0:
                raise GMachineException("bad delay")
            hal.join()
            time.sleep(pause)
        elif c == 'G17':  # XY plane select
            self._plane = PLANE_XY
        elif c == 'G18':  # ZX plane select
            self._plane = PLANE_ZX
        elif c == 'G19':  # YZ plane select
            self._plane = PLANE_YZ
        elif c == 'G20':  # switch to inches
            self._convertCoordinates = 25.4
        elif c == 'G21':  # switch to mm
            self._convertCoordinates = 1.0
        elif c == 'G28':  # home
            axises = gcode.has('X'), gcode.has('Y'), gcode.has('Z')
            if axises == (False, False, False):
                axises = True, True, True
            self.safe_zero(*axises)
            hal.join()
            if not hal.calibrate(*axises):
                raise GMachineException("failed to calibrate")
        elif c == 'G53':  # switch to machine coords
            raise GMachineException('Not supported')
            # TODO not sure what local/machine coordinates mean and how to handle this with multiple extruders
            # self._local = Coordinates(0.0, 0.0, 0.0, 0.0)
        elif c == 'G90':  # switch to absolute coords
            self._absoluteCoordinates = True
        elif c == 'G91':  # switch to relative coords
            self._absoluteCoordinates = False
        elif c == 'G92':  # switch to local coords
            raise GMachineException('Not supported')
            # if gcode.has_coordinates():
            #     self._local = self._position - gcode.coordinates(
            #         Coordinates(self._position.x - self._local.x,
            #                     self._position.y - self._local.y,
            #                     self._position.z - self._local.z,
            #                     self._position.e - self._local.e),
            #         self._convertCoordinates)
            # else:
            #     self._local = self._position
        elif c == 'M2' or c == 'M30':  # program finish, reset everything.
            self.reset()
        elif c == 'M72':
            audio_id = int(gcode.get('P', 0))
            if audio_id not in AUDIO_FILES:
                raise GMachineException('Audio ID not recognized')
            audio_filepath = AUDIO_BASE_FILEPATH + AUDIO_FILES[audio_id]
            logging.info('playing audio from {}'.format(audio_filepath))
            AudioPlayer.play(audio_filepath)
        elif c == 'M84':  # disable motors
            hal.disable_steppers()
        elif c == 'M111':  # enable debug
            logging_config.debug_enable()
        elif c == 'M114':  # get current position
            hal.join()
            p = self.position()
            answer = "X:{} Y:{} Z:{} E:{}".format(p.x, p.y, p.z, p.e)
        elif c == 'T':  # select tool (extruder)
            self._set_extruder(int(gcode.get('T')))
        elif c is None:  # command not specified(ie just F was passed)
            pass
        # commands below are added just for compatibility
        elif c == 'M82':  # absolute mode for extruder
            if not self._absoluteCoordinates:
                raise GMachineException("Not supported, use G90/G91")
        elif c == 'M83':  # relative mode for extruder
            if self._absoluteCoordinates:
                raise GMachineException("Not supported, use G90/G91")
        else:
            raise GMachineException("unknown command")
        # save parameters on success
        self._velocity = velocity
        logging.debug("position {}".format(self._position))
        return answer

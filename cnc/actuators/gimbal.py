from threading import Timer

class GimbalMotor(object):
    """
    GimbalMotor tracks the current angle of a ServoMotor and provides options to wait until the motor reaches the
    specified angle. Because there is no sensor to actually measure this, waiting until the motor stops is implemented
    by a constant delay after each call to `set_angle`.
    """

    def __init__(self, servo_motor, range=180.0, delay=1.0):
        """
        Arguments:
            servo_motor {ServoMotor} -- the underlying ServoMotor

        Keyword Arguments:
            range {float} -- the range of angles in degrees (default: {90.0})
            delay {float} -- how long (in seconds) it takes to span the range of angles (default: {1.0})
        """
        self._motor = servo_motor
        self._max_angle = range / 2.0
        self._delay = delay
        self._timer = None
        self._angle = 0

    def _on_complete(self):
        pass

    def set_angle(self, angle, wait=False, interrupt=False):
        """
        Set the angle of the gimbal motor

        Arguments:
            angle {float} -- what angle to move the gimbal motor to, where angle ranges from plus or minus half the
                total range (degrees)

        Keyword Arguments:
            wait {bool} -- True iff the function should not return until the motor stops (default: {False})
            interrupt {bool} -- False iff this function should wait until the motor stops before setting the next angle
                (default: {False})

        Raises:
            ValueError -- if the input angle is out of range
        """
        if angle < -self._max_angle or angle > self._max_angle:
            raise ValueError('set angle out of range')

        # wait until the motor stops moving, unless its okay to interrupt
        if not interrupt and self._timer:
            self._timer.join()

        self._motor.set(angle / self._max_angle)
        self._timer = Timer(self._delay, self._on_complete)
        self._timer.start()
        self._angle = angle

        # optionally wait until the motor stops moving
        if wait:
            self._timer.join()

    def get_angle(self):
        """
        Wait until the motor stops, then return its angle

        Returns:
            float -- the current angle where angle ranges from plus or minus half the total range (degrees)
        """
        self.join()
        return self._angle

    def join(self):
        """
        Wait until the motor stops
        """
        if self._timer:
            self._timer.join()

    def release(self):
        """
        Stop holding any angle
        """
        self._motor.stop()


class Gimbal(object):
    def __init__(self, *motors):
        """
        Arguments:
            *motors {GimbalMotor[]} -- a GimbalMotor for each axis of the gimbal

        Raises:
            ValueError -- if motors is empty
        """
        if not motors:
            raise ValueError('A gimbal must have at least one axis')
        self._motors = motors

    def set_position(self, *angles, wait=False, interrupt=False):
        """
        Set the gimbal to an angular position

        Arguments:
            *angles {float[]} -- what angle to move each axis of the gimbal to where angle ranges from plus or minus
                half the total range (degrees)

        Keyword Arguments:
            wait {bool} -- True iff the function should not return until the gimbal stops (default: {False})
            interrupt {bool} -- False iff this function should wait until the gimbal stops before setting the next
                position (default: {False})

        Raises:
            ValueError -- if the wrong number of angles are supplied
        """
        if len(angles) != len(self._motors):
            raise ValueError('Wrong number of angles for gimbal')

        if not interrupt:
            self.join()

        for i, motor in enumerate(self._motors):
            angle = angles[i]
            motor.set_angle(angle)

        if wait:
            self.join()

    def get_position(self):
        """
        Wait until the gimbal stops, then return its position

        Returns:
            float[] -- the angle of each axis, where angle ranges from plus or minus half the total range (degrees)
        """
        return [motor.get_angle() for motor in self._motors]

    def join(self):
        for motor in self._motors:
            motor.join()

    def release(self):
        for motor in self._motors:
            motor.release()

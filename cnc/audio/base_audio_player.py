import os

from abc import ABC, abstractmethod


class BaseAudioPlayer(ABC):
    @classmethod
    @abstractmethod
    def play(cls, filepath):
        """
        Play a .wav file asynchronously

        Arguments:
            filepath {str} -- a path to a WAV file
        """
        pass

    @classmethod
    @abstractmethod
    def stop(cls):
        """
        Stop any currently playing sound
        """
        pass


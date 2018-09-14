import pygame
import pygame.mixer as mixer

from cnc.audio.base_audio_player import BaseAudioPlayer


_initialized = False
try:
    mixer.init()
    _initialized = True
except pygame.error as e:
    # catch the error for when no device is detected
    # this can happen when a bluetooth device is not connected, for example
    print(e)

class PygameAudioPlayer(BaseAudioPlayer):
    """
    Play sound files with pygame
    """

    _prev_filepath = None

    @classmethod
    def play(cls, filepath):
        if not _initialized:
            return
        if filepath is not cls._prev_filepath:
            mixer.music.load(filepath)
        mixer.music.play()

    @classmethod
    def stop(cls):
        if not _initialized:
            return
        mixer.music.stop()

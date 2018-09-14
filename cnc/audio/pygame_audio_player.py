import pygame.mixer as mixer

from cnc.audio.base_audio_player import BaseAudioPlayer


mixer.init()

class PygameAudioPlayer(BaseAudioPlayer):
    """
    Play sound files with pygame
    """

    _prev_filepath = None

    @classmethod
    def play(cls, filepath):
        if filepath is not cls._prev_filepath:
            mixer.music.load(filepath)
        mixer.music.play()

    @classmethod
    def stop(cls):
        mixer.music.stop()

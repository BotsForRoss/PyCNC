import winsound

from cnc.audio.base_audio_player import BaseAudioPlayer


class WinsoundAudioPlayer(BaseAudioPlayer):
    """
    Play .wav files with winsound (Windows)
    """
    @classmethod
    def play(cls, filepath):
        winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)

    @classmethod
    def stop(cls):
        winsound.PlaySound(None, 0)

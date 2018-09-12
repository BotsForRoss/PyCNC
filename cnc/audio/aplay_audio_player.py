from cnc.audio.base_audio_player import BaseAudioPlayer
from subprocess import Popen, DEVNULL


class AplayAudioPlayer(BaseAudioPlayer):
    """
    Play .wav files with the aplay command-line audio file player (Linux)
    """

    _process = None

    @classmethod
    def play(cls, filepath):
        # If the audio is still playing, stop it
        # Mixing in aplay is tricky, so let's just run one at a time
        cls.stop()

        cls._process = Popen(['aplay', filepath, '-q'])

    @classmethod
    def stop(cls):
        if cls._process and cls._process.poll() is None:
            cls._process.terminate()

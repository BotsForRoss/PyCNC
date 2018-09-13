import os

if os.name == 'nt':
    from cnc.audio.winsound_audio_player import WinsoundAudioPlayer as AudioPlayer
else:
    from cnc.audio.aplay_audio_player import AplayAudioPlayer as AudioPlayer

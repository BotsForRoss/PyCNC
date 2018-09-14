import os

try:
    from cnc.audio.pygame_audio_player import PygameAudioPlayer as AudioPlayer
except ImportError as e:
    print(e)
    if os.name == 'nt':  # Windows
        from cnc.audio.winsound_audio_player import WinsoundAudioPlayer as AudioPlayer
    else:
        from cnc.audio.aplay_audio_player import AplayAudioPlayer as AudioPlayer

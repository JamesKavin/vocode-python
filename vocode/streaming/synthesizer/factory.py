import logging
from typing import Optional
import typing

from vocode.streaming.models.synthesizer import (
    AzureSynthesizerConfig,
    CoquiTTSSynthesizerConfig,
    ElevenLabsSynthesizerConfig,
    GTTSSynthesizerConfig,
    GoogleSynthesizerConfig,
    PlayHtSynthesizerConfig,
    RimeSynthesizerConfig,
    StreamElementsSynthesizerConfig,
    SynthesizerConfig,
    SynthesizerType,
)
from vocode.streaming.synthesizer.azure_synthesizer import AzureSynthesizer
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer
from vocode.streaming.synthesizer.google_synthesizer import GoogleSynthesizer
from vocode.streaming.synthesizer.gtts_synthesizer import GTTSSynthesizer
from vocode.streaming.synthesizer.play_ht_synthesizer import PlayHtSynthesizer
from vocode.streaming.synthesizer.rime_synthesizer import RimeSynthesizer
from vocode.streaming.synthesizer.stream_elements_synthesizer import (
    StreamElementsSynthesizer,
)
from vocode.streaming.synthesizer.coqui_tts_synthesizer import CoquiTTSSynthesizer


class SynthesizerFactory:
    def create_synthesizer(
        self,
        synthesizer_config: SynthesizerConfig,
        logger: Optional[logging.Logger] = None,
    ):
        if isinstance(synthesizer_config, GoogleSynthesizerConfig):
            return GoogleSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, AzureSynthesizerConfig):
            return AzureSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, ElevenLabsSynthesizerConfig):
            return ElevenLabsSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, PlayHtSynthesizerConfig):
            return PlayHtSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, RimeSynthesizerConfig):
            return RimeSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, GTTSSynthesizerConfig):
            return GTTSSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, StreamElementsSynthesizerConfig):
            return StreamElementsSynthesizer(synthesizer_config, logger=logger)
        elif isinstance(synthesizer_config, CoquiTTSSynthesizerConfig):
            return CoquiTTSSynthesizer(synthesizer_config, logger=logger)
        else:
            raise Exception("Invalid synthesizer config")

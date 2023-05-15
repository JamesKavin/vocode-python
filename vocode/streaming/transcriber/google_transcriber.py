import asyncio
import logging
import os
import time
import queue
from typing import Optional
import threading
from vocode import getenv

from vocode.streaming.models.audio_encoding import AudioEncoding
from vocode.streaming.transcriber.base_transcriber import (
    BaseThreadAsyncTranscriber,
    Transcription,
)
from vocode.streaming.models.transcriber import GoogleTranscriberConfig
from vocode.streaming.utils import create_loop_in_thread


class GoogleTranscriber(BaseThreadAsyncTranscriber):
    def __init__(
        self,
        transcriber_config: GoogleTranscriberConfig,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(transcriber_config)

        from google.cloud import speech

        self.speech = speech

        self._ended = False
        credentials_path = getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise Exception(
                "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable"
            )
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.google_streaming_config = self.create_google_streaming_config()
        self.client = self.speech.SpeechClient()
        self.is_ready = False
        if self.transcriber_config.endpointing_config:
            raise Exception("Google endpointing config not supported yet")

    def create_google_streaming_config(self):
        extra_params = {}
        if self.transcriber_config.model:
            extra_params["model"] = self.transcriber_config.model
            extra_params["use_enhanced"] = True

        if self.transcriber_config.language_code:
            extra_params["language_code"] = self.transcriber_config.language_code

        if self.transcriber_config.audio_encoding == AudioEncoding.LINEAR16:
            google_audio_encoding = self.speech.RecognitionConfig.AudioEncoding.LINEAR16
        elif self.transcriber_config.audio_encoding == AudioEncoding.MULAW:
            google_audio_encoding = self.speech.RecognitionConfig.AudioEncoding.MULAW

        return self.speech.StreamingRecognitionConfig(
            config=self.speech.RecognitionConfig(
                encoding=google_audio_encoding,
                sample_rate_hertz=self.transcriber_config.sampling_rate,
                **extra_params
            ),
            interim_results=True,
        )

    def run(self):
        stream = self.generator()
        requests = (
            self.speech.StreamingRecognizeRequest(audio_content=content)
            for content in stream
        )
        responses = self.client.streaming_recognize(
            self.google_streaming_config, requests
        )
        self.process_responses_loop(responses)

    def terminate(self):
        self._ended = True

    def process_responses_loop(self, responses):
        for response in responses:
            self._on_response(response)

            if self._ended:
                break

    def _on_response(self, response):
        if not response.results:
            return

        result = response.results[0]
        if not result.alternatives:
            return

        top_choice = result.alternatives[0]
        message = top_choice.transcript
        confidence = top_choice.confidence

        self.output_janus_queue.sync_q.put_nowait(
            Transcription(message, confidence, result.is_final)
        )

    def generator(self):
        while not self._ended:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self.input_janus_queue.sync_q.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self.input_janus_queue.sync_q.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

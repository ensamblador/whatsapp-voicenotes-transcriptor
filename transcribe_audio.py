import os
import json
import asyncio
import aiofile

from amazon_transcribe.auth import  StaticCredentialResolver
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.utils import apply_realtime_delay

AWS_ACCESS_KEY_ID                    = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY                = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN                    = os.environ.get('AWS_SESSION_TOKEN')


creds = StaticCredentialResolver(
    access_key_id=AWS_ACCESS_KEY_ID,
    secret_access_key=AWS_SECRET_ACCESS_KEY,
    session_token=AWS_SESSION_TOKEN
)


SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2
CHANNEL_NUMS = 1
LANGUAGE_CODE = 'es-US'
MEDIA_ENCODING = 'flac'

AUDIO_PATH = './output3.flac'
CHUNK_SIZE = 1024 * 16
REGION = "us-east-1"
TRANSCRIPTION = ""


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
        global TRANSCRIPTION
        results = transcript_event.transcript.results
        for result in results:
            if result.is_partial == False:
                for alt in result.alternatives:
                    TRANSCRIPTION += alt.transcript
                    print(alt.transcript)



async def basic_transcribe():
    # Setup up our client with our chosen AWS region
    client = TranscribeStreamingClient(region=REGION)

    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code=LANGUAGE_CODE,
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding=MEDIA_ENCODING,
    )

    async def write_chunks():
        # NOTE: For pre-recorded files longer than 5 minutes, the sent audio
        # chunks should be rate limited to match the realtime bitrate of the
        # audio stream to avoid signing issues.
        async with aiofile.AIOFile(AUDIO_PATH, "rb") as afp:
            reader = aiofile.Reader(afp, chunk_size=CHUNK_SIZE)
            async for chunk in reader:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()

    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())


loop = asyncio.get_event_loop()
loop.run_until_complete(basic_transcribe())
loop.close()

print("transcript:",TRANSCRIPTION)
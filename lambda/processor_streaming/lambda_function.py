import os
import subprocess
import shlex
import time

import base64


import json
import asyncio
import aiofile 

from amazon_transcribe.auth import  StaticCredentialResolver
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.utils import apply_realtime_delay


SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2
CHANNEL_NUMS = 1
LANGUAGE_CODE = 'es-US'
MEDIA_ENCODING = 'flac'

#AUDIO_PATH = './output3.flac'
CHUNK_SIZE = 1024 * 24
REGION = "us-east-1"
LOCAL_FOLDER              = '/tmp/'

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
                    TRANSCRIPTION += alt.transcript + " "
                    print(alt.transcript)



async def basic_transcribe(file_name):
    # Setup up our client with our chosen AWS region
    client = TranscribeStreamingClient(region=REGION)

    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code=LANGUAGE_CODE,
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding=MEDIA_ENCODING,
    )

    async def write_chunks(filename):
        # NOTE: For pre-recorded files longer than 5 minutes, the sent audio
        # chunks should be rate limited to match the realtime bitrate of the
        # audio stream to avoid signing issues.
        async with aiofile.AIOFile(filename, "rb") as afp:
            reader = aiofile.Reader(afp, chunk_size=CHUNK_SIZE)
            async for chunk in reader:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()


    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(file_name), handler.handle_events())

def save_m4a_file(event):
    body = json.loads(event['body'])
    print(body)
    audio64 = body['audio']
    audio_decoded = base64.b64decode(audio64)

    now = int( time.time() )
    LOCAL_FILE = f"audio_{now}.m4a"

    FULL_PATH = f"{LOCAL_FOLDER}{LOCAL_FILE}"

    with open(FULL_PATH, "wb") as binary_file:
        binary_file.write(audio_decoded) 


    return FULL_PATH


def lambda_handler(event, context):
    start = int( time.time() )

    global TRANSCRIPTION
    TRANSCRIPTION = "Transcripción Stream: "
    #return build_response(200, f'<html><head><meta charset="utf-8"></head><body><p>{TRANSCRIPTION}</p></body></html>')

    location = save_m4a_file(event)
    destination = location.replace('.m4a','.flac')

    ffmpeg_command = f"/opt/bin/ffmpeg -i {location} -ar 16000 {destination}"
    command1 = shlex.split(ffmpeg_command)
    p1 = subprocess.run(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(basic_transcribe(destination))
    loop.close()
    print ('final:', TRANSCRIPTION)
    end = int( time.time() )
    duration = end-start
    return build_response(200, f'<html><head><meta charset="utf-8"></head><body><p> {TRANSCRIPTION}</p>({duration}s)</body></html>')


def build_response(status_code, json_content):
        return {
        'statusCode': status_code,
        "headers": {
            "Content-Type": "text/html;charset=UTF-8",
            "charset": "UTF-8",
            "Access-Control-Allow-Origin": "*"
        },
        'body': json_content
    }

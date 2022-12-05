import json
import uuid
import decimal
import os
import boto3
import io
import base64


import time

from s3_functions import sube_archivo
transcribe_client = boto3.client('transcribe')
s3 = boto3.client('s3')


BUCKET                    = os.environ.get('BUCKET')
LOCAL_FOLDER              = '/tmp/'
TRANSCRIPTION = ""


def lambda_handler(event, context):
    start = int( time.time() )
    global TRANSCRIPTION
    TRANSCRIPTION = "Transcripción Stream: "

    body = json.loads(event['body'])
    print(body)
    audio64 = body['audio']
    audio_decoded = base64.b64decode(audio64)

    now = int( time.time() )
    
    LOCAL_FILE = f"audio_{now}.m4a"
    with open(f"{LOCAL_FOLDER}{LOCAL_FILE}", "wb") as binary_file:
        binary_file.write(audio_decoded) 
    sube_archivo(LOCAL_FOLDER,LOCAL_FILE, BUCKET, LOCAL_FILE)
    
    transcription = transcribe_file(
        f'{LOCAL_FILE}_job', f"s3://{BUCKET}/{LOCAL_FILE}", 
        BUCKET,
        transcribe_client)

    end = int( time.time() )
    duration = end-start
    return build_response(200, f'<html><head><meta charset="utf-8"></head><body><p>{transcription}</p>({duration}s)</body></html>')


def transcribe_file(job_name, file_uri, output_bucket, transcribe_client ):
    transcribe_client.start_transcription_job(
        
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        OutputBucketName=output_bucket,
        OutputKey=f'{job_name}_transcription.json',
        MediaFormat='mp4',
        LanguageCode='es-US'
    )

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            print(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                transcript = get_transcript(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
            
                
                print(
                    f"Download the transcript from\n"
                    f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")

                print (f'transcript:{transcript}')
                return transcript
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(1)


def get_transcript(transcript):
        parts = transcript.split('https://')[1].split('/')
        bucket = parts[1]
        key = parts[2]
        data = s3.get_object(Bucket=bucket, Key=key)
        contents = data['Body'].read()
        transc = json.loads(contents.decode())
        return ''.join([tr['transcript'] for tr in transc['results']['transcripts']])


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

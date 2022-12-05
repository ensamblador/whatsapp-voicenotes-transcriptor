from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_iam,
    RemovalPolicy

    # aws_sqs as sqs,
)
from constructs import Construct
from api_cors.api_cors import api_cors_lambda



class WhatsappVoicenotesTranscriptorStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        audio_bucket = s3.Bucket(self, 'audios', versioned=False, removal_policy=RemovalPolicy.DESTROY)


        aiofile_transcribe_layer = _lambda.LayerVersion(
            self, "aiofile-transcribe", code=_lambda.Code.from_asset("./lambda/layers/aiofile-amazon-transcribe.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8,_lambda.Runtime.PYTHON_3_9], 
            description = 'aiofile y amazon-transcribe', layer_version_name = "aiofile-transcribe-streamig"
        )

        ffmpeg_layer = _lambda.LayerVersion(
            self, "ffmpeg", code=_lambda.Code.from_asset("./lambda/layers/ffmpeg.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8,_lambda.Runtime.PYTHON_3_9], 
            description = 'ffmpeg', layer_version_name = "ffmpeg"
        )

        process_function = _lambda.Function(self, "audio", runtime=_lambda.Runtime.PYTHON_3_9,
                                          handler="lambda_function.lambda_handler", timeout=Duration.seconds(900),
                                          memory_size=3008, code=_lambda.Code.from_asset("./lambda/processor"),
                                          environment = {'BUCKET': audio_bucket.bucket_name},
                                          description='Procesa el audio de Whatsapp')

        streaming_function = _lambda.Function(self, "audio-stream", runtime=_lambda.Runtime.PYTHON_3_8,
                                          handler="lambda_function.lambda_handler", timeout=Duration.seconds(900),
                                          memory_size=3008, code=_lambda.Code.from_asset("./lambda/processor_streaming"),
                                          environment = {'BUCKET': audio_bucket.bucket_name},
                                          layers = [aiofile_transcribe_layer, ffmpeg_layer],
                                          description='Procesa el audio de Whatsapp en streaming')

        process_function.add_to_role_policy(aws_iam.PolicyStatement( actions=["transcribe:*",], resources=['*']))
        streaming_function.add_to_role_policy(aws_iam.PolicyStatement( actions=["transcribe:*",], resources=['*']))

        audio_bucket.grant_read_write(process_function)
        audio_bucket.grant_read_write(streaming_function)


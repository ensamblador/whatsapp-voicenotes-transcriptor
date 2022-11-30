import aws_cdk as core
import aws_cdk.assertions as assertions

from whatsapp_voicenotes_transcriptor.whatsapp_voicenotes_transcriptor_stack import WhatsappVoicenotesTranscriptorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in whatsapp_voicenotes_transcriptor/whatsapp_voicenotes_transcriptor_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WhatsappVoicenotesTranscriptorStack(app, "whatsapp-voicenotes-transcriptor")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

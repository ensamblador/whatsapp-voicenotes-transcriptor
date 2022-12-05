
import boto3
s3client = boto3.client('s3')

def descarga_archivo(bucket, key, base_path, filename):
    with open(base_path+filename, "wb") as data:
        s3client.download_fileobj(bucket, key, data)
    return True

def sube_archivo(path, filename, bucket, key):
    with open(path+filename, 'rb') as data:
        s3client.upload_fileobj(data,bucket, key)
    
    list_response = list_s3_document(bucket, key)

    return list_response

def borra_archivo(bucket, key):
    s3client.delete_object(Bucket=bucket, Key=key)
    return True


def list_s3_document(s3_bucket, s3_key):
    list_response = s3client.list_objects_v2(
        Bucket=s3_bucket,
        MaxKeys=1,
        Prefix=s3_key
    )

    if 'Contents' in list_response:
        return list_response['Contents'][0]
    else:
        return None


def list_all_s3_document(s3_bucket, s3_key):
    list_response = s3client.list_objects_v2(
        Bucket=s3_bucket,
        Prefix=s3_key
    )
    if 'Contents' in list_response:
        file_list = sorted(list_response['Contents'], key= lambda d: d['LastModified'], reverse=True)
        return file_list
    else:
        return []
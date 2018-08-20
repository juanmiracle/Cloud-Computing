import time
import boto3
import json

def test():
    data = {"job_id": '960189de-cea3-4bd9-af78-f7d58f13577a',
        "username": 'testBee',
        "description": 'testBee',
        "user_email" : 'juanmiracle@gmail.com',
        "user_role" : 'free_user',
        "s3_inputs_bucket" :  'gas-inputs',
        "s3_key_input_file" : 'juanmiracle/960189de-cea3-4bd9-af78-f7d58f13577a~test.vcf',
        "input_file_name" : 'test.vcf',
        "s3_results_bucket": 'gas-results',
        "submit_time": int(time.time()),
        "job_status": 'PENDING' 
      }

    sns = boto3.resource('sns')
    job_request_topic = 'arn:aws:sns:us-east-1:127134666975:juanmiracle_job_notifications'
    topic = sns.Topic(job_request_topic)
    topic.publish(Message=json.dumps(data))

if __name__ == "__main__":
    num = 0
    while True:
        test()
        num += 1
        print num

from __future__ import print_function

import boto3
import MySQLdb
from utils_config import *


sqs = boto3.resource('sqs')
s3 = boto3.resource('s3')
queue = sqs.get_queue_by_name(QueueName= result_sqs)
mail_client = boto3.client('ses')


while True:
    # Attempt to read a message from the queue
    # Use long polling - DO NOT use sleep() to wait between polls
     # print("Asking SQS for up to 10 messages...")
    # Get messages
    messages = queue.receive_messages(MaxNumberOfMessages=10)

    # If get the  message, extract job parameters from the message body
    if len(messages) > 0:
        print("Received " + str(len(messages)) + " messages...")
        # Iterate each message
        for message in messages:
            try:
                # Parse JSON message (going two levels deep to get the embedded message)
                msg_body = eval(eval(message.body)['Message'])
    
                # get the user info from the message
                print("msg_body", msg_body)
                job_id = msg_body['job_id']
                username = msg_body['username']
                email = msg_body['user_email']

                # polls the SQS results queue, and sends an email to the user when their job is complete.
                # send email using template string
                # send_email: send_email:http://boto.cloudhackers.com/en/latest/ses_tut.html  
                title_data = 'Hello {}, '.format(username)
                body_data = u'You are receiving this email because your job of :{} on GAS has completed! To check the result and log please click (or go to),\
                                https://juanmiracle.ucmpcs.org:4433/annotations/{}'.format(job_id, job_id)
    
                source = cnetid + "@ucmpcs.org"
                res = mail_client.send_email(Source= source, Destination={'ToAddresses': [email]},
                                             Message={'Subject': {'Data': title_data, 'Charset': 'UTF-8'},
                                                      'Body': {
                                                        'Html': {
                                                          'Data': body_data
                                                            }
                                                        } 
                                                    }
                                            )
    
                print("send ", job_id, "notification to ", email) 
                #delete the message from the queue 
                message.delete()
            except Exception as e:
                print ("Oops!! Something Wrong! Cann't send the email")
    else:
        continue

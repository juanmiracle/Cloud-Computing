#the new job_runner.py
#__author__ = 'Vas Vasiliadis <vas@uchicago.edu>' 
#this file is written based on the in class solution py program 
import boto3
import json
import time
import sys
import getopt
import subprocess
import os
from anno_config import *

# Connect to SQS and get queue
sqs = boto3.resource('sqs')
s3 = boto3.resource('s3')
queue = sqs.get_queue_by_name(QueueName=request_sqs)

# Poll the message queue in a loop 
while True:

	# Attempt to read a message from the queue
	# Use long polling - DO NOT use sleep() to wait between polls
	print "Asking SQS for up to 10 messages."
	# Get messages
	messages = queue.receive_messages(MaxNumberOfMessages=10)
	#if get the message 
	if len(messages) > 0:
		print("Received " + str(len(messages)) + " messages...")
		# Iterate each message
		for message in messages:
			# Parse JSON message (going two levels deep to get the embedded message)
			msg_body = eval(eval(message.body)['Message'])
			#get the message
			key = msg_body['s3_key_input_file']
			print "key" , key 

			job_id = msg_body['job_id']
			input_bucket = msg_body['s3_inputs_bucket']
			bucket = s3.Bucket(input_bucket)
			#get the user information from the seg_body
			username = msg_body['username']
			email = msg_body['user_email']

			try:
                
                #find the filename for the key string  incode is '%'  but it decode to '/'
                filename = key.split('/')[1]
                print "file name", filename
				#http://boto3.readthedocs.org/en/latest/reference/customizations/s3.html
				#download the file from the s3 bucket 
				bucket.download_file(key, filename)
				curPath = os.getcwd()
				newPath_File = os.path.join(curPath,filename)
				print "newPath_File ", newPath_File
				# spawn the subprocess using subprocess package 
				
				process = subprocess.Popen([sys.executable, 'run.py', newPath_File, filename, username, email])
			except Exception as e:
					job_status = 'FAILED'
					print ("job failed! but no message delete")
					print e
			else :
				# If the job is submitted, then delete the message from the queue and continue polling
				#if nothing wrong, delete the message 
				job_status = 'RUNNING'
				print ("Deleting message...")
				message.delete()
			finally:
				# finally, update the jon status in the dynamo_db 
				dynamo_db = boto3.resource('dynamodb')
				table = dynamo_db.Table(annotations_table)
				response = table.update_item(
				Key = {'job_id':job_id}, 
				UpdateExpression="set job_status = :job_status",
				ExpressionAttributeValues={
						':job_status': job_status,
						},
						ReturnValues="UPDATED_NEW"
				)
				print "updateItem succeeded"
	else:
		continue

import sys
import time
import driver
import boto3
import glob
import os
import requests
from boto3.dynamodb.conditions import Key, Attr
from anno_config import *
import json

class Timer(object):
	def __init__(self, verbose=False):
		self.verbose = verbose

	def __enter__(self):
		self.start = time.time()
		return self

	def __exit__(self, *args):
		self.end = time.time()
		self.secs = self.end - self.start
		self.msecs = self.secs * 1000  # millisecs
		if self.verbose:
			print "Elapsed time: %f ms" % self.msecs
# http://docs.aws.amazon.com/amazondynamodb/latest/gettingstartedguide/GettingStarted.Python.03.html#GettingStarted.Python.03.03
# this reference is for update the table item 
def getStatus(jobID, job_status, result_file, log_file, username):
	dynamo_db = boto3.resource('dynamodb')
	table = dynamo_db.Table(annotations_table)
	if job_status == "COMPLETED":
		response = table.update_item(
			Key = {'job_id':jobID}, 
			UpdateExpression="set job_status = :job_status, username = :username, s3_results_bucket= :bucket, s3_key_result_file = :result_file, s3_key_log_file= :log_file, complete_time = :complete_time",
			ExpressionAttributeValues={
					':job_status': job_status,
					':username' : username,
					':bucket': results_bucket,
					':result_file' : result_file,
					':log_file' : log_file,
					':complete_time' : int(time.time())
					},
					ReturnValues="UPDATED_NEW"
			)
		print "update the item successfully"
	else:
		resonse = table.update_item(Key={'job_id': jobID},
									AttributeUpdates={'job_status': {'Value': job_status, 'Action': 'PUT'}})
		if resonse['ResponseMetadata']['HTTPStatusCode'] != 200: 
			raise Exception

if __name__ == '__main__':
	
	#Call the AnnTools pipeline
	try:
		#len(sys.argv) > 1:
		# get the file name 
		input_file_name = sys.argv[1]
		fileID_name = sys.argv[2]
		jobID = fileID_name.split('~')[0].split('/')[-1]
		print "input file name ", input_file_name

		#get user info, and submit then to the result  SQS
		username = sys.argv[3]
		email = sys.argv[4]

	
		with Timer() as t:
			driver.run(input_file_name, 'vcf')

		#print "Total runtime: %s seconds" % t.secs
		# Add code here to save results and log files to S3 results bucket
		s3 = boto3.resource('s3')
		bucket = s3.Bucket(results_bucket)
		
		logPath = '%s.count.log' %fileID_name 
		annotPath = '%s.annot.%s'%(fileID_name.split('.')[0], fileID_name.split('.')[1])

		logFile = glob.glob(logPath)
		annotFile = glob.glob(annotPath)
		
		log_file_path = folder + logPath
		annot_file_path = folder + annotPath
		print "logpath", logPath 
		print "log_file_path", log_file_path
		print "annot_file_path", annot_file_path

		#upload the log file 
		if len(logFile) > 0:
			print "Within run.py: "
			print logFile[0]
			log = logFile[0]
	
			key = os.path.join(folder, log)
			log_file_path = folder + log
			s3.Object(results_bucket,key).upload_file(log)
			#using string!!!!!!!!

		#upload the result file 
		if len(annotFile) > 0:
			annot = annotFile[0]
			key = os.path.join(folder, annot)
			s3.Object(results_bucket,key).upload_file(annot)	


		#publishes a notification to result SNS topic when the job is completed 
		complete_time = int(time.time())
		# Send message to results notifier SQS 
		result_data = { "job_id" : jobID,
						"username": username,
						"complete_time": complete_time,
						"user_email" : email,
					  }

		sns = boto3.resource('sns')
		topic = sns.Topic(job_complete_topic)
		topic.publish(Message=json.dumps(result_data))

	except Exception as e:
		print e
		print 'A  valid .vcf file must be provided as input to this program!'
		#exception, so the job_status = 'Failed'
		getStatus(jobID, 'FAILED', annot_file_path, log_file_path, username)

	else:
		# successfully finished the uoload, so the job_status = 'Completed'
		getStatus(jobID, 'COMPLETED', annot_file_path, log_file_path, username)
		# publish a message to glacier queue for the archive file 
		archive_data = {"job_id":jobID, "username":username, "complete_time":complete_time, "s3_key_result_file": annot_file_path, "type":"archive"}
		glacier_topic = sns.Topic(job_glacier_topic)
		glacier_topic.publish(Message=json.dumps(archive_data))
		print "Ready to archive jobs : " + annot_file_path


	finally:

		#Clean up (delete) local job files
		deleteFile = '%s*'%jobID
		deleteFileName = glob.glob(deleteFile)
		for files in deleteFileName:
			os.remove(files)

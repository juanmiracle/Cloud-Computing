import boto3

sqs = boto3.resource('sqs')
s3 = boto3.resource('s3')
queue1 = sqs.get_queue_by_name(QueueName = 'juanmiracle_job_requests')
queue = sqs.get_queue_by_name(QueueName = 'juanmiracle_glacier_queue')

while True:
	messages = queue.receive_messages(MaxNumberOfMessages = 10)

	for message in messages:
		message.delete()

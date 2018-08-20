from __future__ import print_function
import boto3
import MySQLdb
from utils_config import *
import time
import botocore
#connect to SQS and get the queue 
sqs = boto3.resource('sqs')
s3 = boto3.resource('s3')
queue = sqs.get_queue_by_name(QueueName=glacier_sqs) 
mail_client = boto3.client('ses')

# connect to RDS database to get job owner's role
def getUserRole(username):
    try:
        # http://mysql-python.sourceforge.net/MySQLdb.html
        conn = MySQLdb.connect(host=rds_host, user=rds_username, passwd=rds_pwd, db=rds_userdb, port=int(rds_port))
        dbcursor = conn.cursor()
        query = "SELECT * FROM users WHERE username=%s"
        dbcursor.execute(query, (username,))
        user = dbcursor.fetchone()
        dbcursor.close()
        role = user[1]
    except Exception as e:
        return "Fail to get user role"
    else:
        return role

def polling():
    while True:
        # Attempt to read a message from the queue
        # Use long polling - DO NOT use sleep() to wait between polls
        # print("Asking SQS for up to 10 messages...")
        # Get messages
        messages = queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=20)
    
        # If get the  message, extract job parameters from the message body
        if len(messages) > 0:
            print("Glacier Received " + str(len(messages)) + " messages...")
            # Iterate each message
            for message in messages:
                # Parse JSON message (going two levels deep to get the embedded message)
                msg_body = eval(eval(message.body)['Message'])

                print ("mesbody ", msg_body)
                # http://boto3.readthedocs.io/en/latest/reference/services/s3.html#bucket
                # deal with the  'restore' message type 
                if msg_body['type'] == 'restore':
                    print ("restore job .. ")
                    key = msg_body['key']
    
                    try:
                        restore_obj = s3.Object(archive_bucket, key)
                        state = restore_obj.storage_class
                        try: 
                            # check the available restore file 
                            restore_obj.load()
    
                        except Exception as e:
                            message.delete()
                            print ("No file need to restore, delete the message")
                            continue
    
                        if not state:
                            state = 'Standard'
    
                        # http://boto3.readthedocs.io/en/latest/reference/services/s3.html#id26
                        # stroe in 'GLACIER' need one day, so the restore for the file and update the job status need more than one day 
                        # if the file is not Glacier or the object does not have a completed or ongoing restoration request.
                        if state != 'GLACIER' or 'ongoing-request="false"' in restore_obj.restore:
                            print(" No GLACIER file, restore file")
                            newFileName = cnetid + '/' + key.split('#')[1]
                            source = archive_bucket + '/' + key
                            s3.Object(results_bucket, newFileName).copy_from(CopySource=source)
                            s3.Object(archive_bucket, key).delete()

                            print ("restore complete, update db...")
                            status = "COMPLETED"
                            # set the ARCHIVED status of a job
                            dynamo_db = boto3.resource('dynamodb')
                            table = dynamo_db.Table(dynamodb_table)
                            job_id = key.split("#")[1].split("~")[0]
                            res = table.update_item(Key={'job_id':job_id}, AttributeUpdates={'job_status':{'Value':status, 'Action':'PUT'}})
                            print ("res", res)
                            # Delete the message from the queue
                            print ("Deleting message...")
                            message.delete()

                    except botocore.exceptions.ClientError as e:
                        print("Error in getting file in gas-archive: " + e)
    
                elif msg_body['type'] == 'archive': 
                    print ("archive job...")
                    # deal with the 'archive' message 
                    # get job_id and username then prepending the username to the object name
                    job_id = msg_body['job_id']
                    username = msg_body['username']
                    filename = msg_body['s3_key_result_file']
                    complete_time = msg_body['complete_time'] 

                    user_role = getUserRole(username)
                    print ("user_role", user_role)
                    # this part have problem, at first, I first check the time limit, and then check the user level
                    # if the user is premium user, delete this message, since, premium user no need to archive the file
                    if user_role == 'premium_user':
                        print ("Premium user! Delete this archive message...")
                        message.delete() 
                        continue
                    
                    # if user if free user, then we need to check the time!!!if is free user and the time > 2h, then archive
                    #then we can check how long the free user have accessed the file
                    newFileName  = cnetid + '/' + username + '#' + filename.split('/')[1]
                    if user_role == 'free_user' and (int(time.time()) - complete_time > free_user_limit_time):
                        print("Time exceed! Archive the file ",newFileName)
                        source = results_bucket + '/' + filename
                        print ("source " + source)
                        s3.Object(archive_bucket, newFileName).copy_from(CopySource= source)
                        s3.Object(results_bucket, filename).delete()
                        status = "ARCHIVED"
                        print ("change the state of the job")
                        
                        try:
                            # set the ARCHIVED status of a job
                            dynamo_db = boto3.resource('dynamodb')
                            table = dynamo_db.Table(dynamodb_table)
                            res = table.update_item(Key={'job_id':job_id}, AttributeUpdates={'job_status':{'Value':status, 'Action':'PUT'}})
                            # Delete the message from the queue
                            print ("Deleting message...")
                            message.delete()
                        except:
                            print ("fail to updatet the job status ! ")

if __name__ == "__main__":
    polling()

# mpcs_app.py
#
# Copyright (C) 2011-2016 Vas Vasiliadis
# University of Chicago
##
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import base64
import datetime
import hashlib
import hmac
import json
import sha
import string
import time
import urllib
import urlparse
import uuid
import boto3
import botocore.session
from boto3.dynamodb.conditions import Key

from mpcs_utils import log, auth
from bottle import route, request, redirect, template, static_file

'''
*******************************************************************************
Set up static resource handler - DO NOT CHANGE THIS METHOD IN ANY WAY
*******************************************************************************
'''
@route('/static/<filename:path>', method='GET', name="static")
def serve_static(filename):
  # Tell Bottle where static files should be served from
  return static_file(filename, root=request.app.config['mpcs.env.static_root'])

'''
*******************************************************************************
Home page
*******************************************************************************
'''
@route('/', method='GET', name="home")
def home_page():
  log.info(request.url)
  return template(request.app.config['mpcs.env.templates'] + 'home', auth=auth)

'''
*******************************************************************************
Registration form
*******************************************************************************
'''
@route('/register', method='GET', name="register")
def register():
  log.info(request.url)
  return template(request.app.config['mpcs.env.templates'] + 'register',
    auth=auth, name="", email="", username="", alert=False)

@route('/register', method='POST', name="register_submit")
def register_submit():
  auth.register(description=request.POST.get('name').strip(),
                username=request.POST.get('username').strip(),
                password=request.POST.get('password').strip(),
                email_addr=request.POST.get('email_address').strip(),
                role="free_user")
  return template(request.app.config['mpcs.env.templates'] + 'register', 
    auth=auth, alert=True)

@route('/register/<reg_code>', method='GET', name="register_confirm")
def register_confirm(reg_code):
  log.info(request.url)
  auth.validate_registration(reg_code)

  return template(request.app.config['mpcs.env.templates'] + 'register_confirm',
    auth=auth)

'''
*******************************************************************************
Login, logout, and password reset forms
*******************************************************************************
'''
@route('/login', method='GET', name="login")
def login():
  log.info(request.url)
  redirect_url = "/annotations"
  # If the user is trying to access a protected URL, go there after auhtenticating
  if request.query.redirect_url.strip() != "":
    redirect_url = request.query.redirect_url

  return template(request.app.config['mpcs.env.templates'] + 'login', 
    auth=auth, redirect_url=redirect_url, alert=False)

@route('/login', method='POST', name="login_submit")
def login_submit():
  auth.login(request.POST.get('username'),
             request.POST.get('password'),
             success_redirect=request.POST.get('redirect_url'),
             fail_redirect='/login')


@route('/logout', method='GET', name="logout")
def logout():
  log.info(request.url)
  auth.logout(success_redirect='/login')


'''
*******************************************************************************
Core GAS code is below...
*******************************************************************************
'''

'''
*******************************************************************************
Subscription management handlers
*******************************************************************************
'''
import stripe

# Display form to get subscriber credit card info
@route('/subscribe', method='GET', name="subscribe")
def subscribe():
    auth.require(fail_redirect='/login?redirect_url=' + request.url)
    if auth.current_user.role != request.app.config['mpcs.plans.free']:
        redirect('/profile')
    return template(request.app.config['mpcs.env.templates'] + "subscribe", auth = auth, user= auth.current_user)

# Process the subscription request
@route('/subscribe', method='POST', name="subscribe_submit")
def subscribe_submit():
    auth.require(fail_redirect='/login')
    try:
        # https://stripe.com/docs/api?lang=python#intro
        # set the stripe secret key, get the token, and create the new customer 
        stripe.api_key = request.app.config['mpcs.stripe.secret_key']
        token = request.POST.get('stripe_token').strip()
        customer = stripe.Customer.create(
                                            card = token,
                                            plan = 'premium_plan',
                                            email = auth.current_user.email_addr,
                                            description = auth.current_user.username)

    except Exception as e:
        print e

    else:
        # update the role of the current user 
        user = auth.current_user
        user.update(role="premium_user")

        print "premium user now!"
        s3 = boto3.resource('s3')
        cnetid = request.app.config['mpcs.auth.cnetid']
        archive_bucket = request.app.config['mpcs.aws.s3.archive_bucket']
        bucket = s3.Bucket(archive_bucket)
        archive_prefix = cnetid + '/' + user.username + '#'
        bucket_objs = bucket.objects.filter(Prefix= archive_prefix)
        #update the user_role for every jobID 

        print "bucket obj", bucket_objs
        # user change the status, so restore the job from the archive 
        # https://github.com/boto/boto3/issues/380

        for one_object in bucket_objs:
            obj = s3.Object(one_object.bucket_name, one_object.key)
            # if obj.restore = None and its type is 'Glacier' then we restore it 
            if not obj.restore:
                if obj.storage_class == 'GLACIER':
                    restore_obj = one_object.restore_object(
                        RequestPayer='requester',
                        RestoreRequest={'Days': 1})
        

            # publish the restore massage to glacier sns
            print "restore the file..."
            data = {"key":obj.key, "job_status": "COMPLETED", "type":"restore"}
            glacier_sns = request.app.config['mpcs.aws.sns.job_glacier_topic']
            sns = boto3.resource('sns')
            topic = sns.Topic(glacier_sns)
            response = topic.publish(Message=json.dumps(data))
    
        return template(request.app.config['mpcs.env.templates'] + "subscribe_confirm", auth = auth, stripe_id=customer['id'])



'''
*******************************************************************************
Display the user's profile with subscription link for Free users
*******************************************************************************
'''
@route('/profile', method='GET', name="profile")
def user_profile():
    auth.require(fail_redirect='/login?redirect_url=' + request.url)
    user = auth.current_user
    return template(request.app.config['mpcs.env.templates'] + "profile", auth = auth, user= user)


'''
*******************************************************************************
Creates the necessary AWS S3 policy document and renders a form for
uploading an input file using the policy document
*******************************************************************************
'''
@route('/annotate', method='GET', name="annotate")
def upload_input_file():
    auth.require(fail_redirect='/login?redirect_url=' + request.url)
    
    #get variable from the mpcs.config
    cnetid = request.app.config['mpcs.auth.cnetid']
    input_bucket = request.app.config['mpcs.aws.s3.inputs_bucket']
    redirecte_url = request.url[:request.url.rfind('/')] + "/annotate/job"
    size = request.app.config['mpcs.plans.free_file_size_limit']
    default_acl = request.app.config['mpcs.aws.s3.default_acl']
    #server_side_encryption = request.app.config['mpcs.aws.s3.server_side_encryption']
    
    # Define S3 policy document, and set the expiration timestamp
    # http://boto3.readthedocs.org/en/latest/reference/core/session.html
    sess = botocore.session.Session()
    cred = sess.get_credentials()
    access_key = cred.access_key
    secret_key = cred.secret_key
    nowtime = datetime.datetime.utcnow()
    expiration_time = nowtime + datetime.timedelta(hours = 3)
    
    # Encode and sign policy document
    # the encode part reference: https://aws.amazon.com/articles/1434
    # conditions: bucket name, key (file) name, and acl. no space
    policy_document = '{"expiration": "%s",'\
        '"conditions":['\
            '{"bucket":"%s"},'\
            '["starts-with", "$key", "juanmiracle/"],'\
            '{"acl": "%s"},'\
            '{"success_action_redirect": "%s"}]}'%(expiration_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'), input_bucket, default_acl, redirecte_url)
    #print "policy document ", policy_document

    policy = base64.b64encode(policy_document.encode('utf-8'))
    #print policy
    # Sign the encoded policy using your AWS secret key with SHA1
    # Take a digest of the signed policy and Encode the digest as base64
    signature = base64.b64encode(hmac.new(secret_key.encode(), policy, hashlib.sha1).digest())
    #print "signature"
    #Render the upload form
    jobID = str(uuid.uuid4())
    res = {'policy' : policy, 'aws_key' : access_key.encode(), 'signature' : signature, 'jobID':jobID}

    return template(request.app.config['mpcs.env.templates'] + "upload",
                bucket_name=input_bucket, username=cnetid, jobid=res['jobID'],
                aws_key=res['aws_key'], policy=res['policy'], signature=res['signature'], acl = default_acl,
                url=redirecte_url, auth=auth, size=size)


'''
*******************************************************************************
Accepts the S3 redirect GET request, parses it to extract 
required info, saves a job item to the database, and then
publishes a notification for the annotator service.
*******************************************************************************
'''
@route('/annotate/job', method='GET')
def create_annotation_job_request():
    auth.require(fail_redirect='/login')

    # check if the request is valid
    try:
        if request.query['etag'][0] != '"':
            raise Exception
    except:
        return HTTPError(403, body='ILLegal Request! ')

    # Get bucket name and key from the S3 redirect URL
    #find the filename for the key string  incode is '%'  but it decode to '/'
    key = request.query['key']
    bucket = key.split('/')[0]
    filename = key.split('/')[1]
    jobID = filename.split('~')[0]
    user = auth.current_user
    input_bucket = request.app.config['mpcs.aws.s3.inputs_bucket']
    result_bucket = request.app.config['mpcs.aws.s3.results_bucket']
  
    # Generate a unique job ID, I also add the role and email in the table, so it will be easier to find the email in annotator 
    # Create a job item and persist it to the annotations database
    data = {"job_id": jobID, 
        "username": user.username,
        "description": user.description,
        "user_email" : user.email_addr,
        "user_role" : user.role,
        "s3_inputs_bucket" :  input_bucket,
        "s3_key_input_file" : key,
        "input_file_name" : filename,
        "s3_results_bucket": result_bucket,
        "submit_time": int(time.time()),
        "job_status": 'PENDING' 
      }
    # Create new request that includes the same data in the body
    dynamodb_table = request.app.config['mpcs.aws.dynamodb.annotations_table']
    sns_arn = request.app.config['mpcs.aws.sns.job_request_topic']
    dynamo_db =boto3.resource('dynamodb')

    table = dynamo_db.Table(dynamodb_table)
    table.put_item(Item = data)
  
    #get sns and send the topic 
    sns = boto3.resource('sns')
    topic = sns.Topic(sns_arn)
    topic.publish(Message = json.dumps(data))
  
  
    return template(request.app.config['mpcs.env.templates'] + "upload_confirm", auth=auth, job_id=jobID)

'''
*******************************************************************************
List all annotations for the user
*******************************************************************************
'''
@route('/annotations', method='GET', name="annotations_list")
def get_annotations_list():
    auth.require(fail_redirect='/login?redirect_url=' + request.url)


    dynamodb_table = request.app.config['mpcs.aws.dynamodb.annotations_table']
    user = auth.current_user
    username = user.username 

    # query specific user's job
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table(dynamodb_table)



    #from the cloud slide, query the table 
    response = table.query(IndexName='username-index', KeyConditionExpression=Key('username').eq(username))
    jobs = response['Items']

    return template(request.app.config['mpcs.env.templates'] + "list_jobs", auth=auth, jobs=jobs)


'''
*******************************************************************************
Display details of a specific annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>', method='GET', name="annotation_details")
def get_annotation_details(job_id):
    auth.require(fail_redirect='/login?redirect_url=' + request.url)
    user = auth.current_user
    result_url = None
    log_content = None
    log_presigned_url = None

    # get the details from the db 
    result_bucket = request.app.config['mpcs.aws.s3.results_bucket']
    dynamodb_table = request.app.config['mpcs.aws.dynamodb.annotations_table']
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table(dynamodb_table)
    res = table.get_item(Key={'job_id': job_id})
    print "res ", res 
    job = res['Item']

    #print "job ", job 
    # check the time 
    try:
      job['submit_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(job['submit_time']))
    except:
        return HTTPError(404, body='No Job has been found')

    # user permission 
    if job['username'] != user.username:
        return HTTPError(403, body='Sorry! Your Permission denied.')


    if job['job_status'] == 'COMPLETED':
        comple_time = job['complete_time']
        job['complete_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(job['complete_time']))

        # generate temporary  download url for given log file
        # https://github.com/boto/boto3/issues/110
        session = botocore.session.get_session()
        client = session.create_client('s3')
        log_presigned_url = client.generate_presigned_url(
            'get_object', 
            Params={'Bucket': result_bucket, 'Key': job['s3_key_log_file']}, 
            ExpiresIn=100
            )


        # Display the log file for an annotation job
        # http://boto3.readthedocs.io/en/latest/guide/resources.html
        s3 = boto3.resource('s3')
        log_obj = s3.Object(result_bucket, job['s3_key_log_file'])

        try:
            # check whether file is passed the time limit
            if int(time.time()) - comple_time <= eval(request.app.config['mpcs.plans.free_time_limit']) \
                    or user.role != request.app.config['mpcs.plans.free']:

                # check whether result file exists in result bucket
                # http://stackoverflow.com/questions/33842944/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
                res = s3.Object(result_bucket, job['s3_key_result_file']).load()
                # generate result file download url
                result_url = client.generate_presigned_url(
                    'get_object', 
                    Params={'Bucket': result_bucket, 'Key': job['s3_key_result_file']},
                    ExpiresIn=100)

        except Exception as e:
            print e

    return template(request.app.config['mpcs.env.templates'] + "job_detail", auth=auth, user=user, job=job,
                    result_url=result_url, log_url=log_presigned_url)

'''
*******************************************************************************
Display the log file for an annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>/log', method='GET', name="annotation_log")
def view_annotation_log(job_id):
    s3 = boto3.resource('s3')
    result_bucket = request.app.config['mpcs.aws.s3.results_bucket']
    dynamodb_table = request.app.config['mpcs.aws.dynamodb.annotations_table']
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table(dynamodb_table)
    res = table.get_item(Key={'job_id': job_id})
    job = res['Item']
    log_obj = s3.Object(result_bucket, job['s3_key_log_file'])
    log_content = log_obj.get()['Body'].read()
    log_content = log_content.replace("\n", '<br/>')
    return log_content


### EOF
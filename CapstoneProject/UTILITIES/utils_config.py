#------------------------------------------------
#Utilities  Default MPCS application configuration settings 
#------------------------------------------------

#[mpcs.auth]
# Change the values below to reflect your RDS installation
db_url = "mysql://juanmiracle:juan1992925@juanmiracle-auth-db.catcuq1wrjmn.us-east-1.rds.amazonaws.com:3306/gasauth"


cnetid = "juanmiracle"
domain = "juanmiracle.ucmpcs.org"
rds_host = "juanmiracle-auth-db.catcuq1wrjmn.us-east-1.rds.amazonaws.com"
rds_port = 3306
rds_username = "juanmiracle"
rds_pwd = "juan1992925"
rds_userdb = "gasauth"


#-----------------------------
# Amazon Web Services settings
#-----------------------------
#[mpcs.aws]
app_region = "us-east-1"

#[mpcs.aws.s3]
inputs_bucket = "gas-inputs"
results_bucket = "gas-results"
archive_bucket = "gas-archive"
default_acl = "private"
free_user_limit_time = 7200


#[mpcs.aws.sqs]
result_sqs = "juanmiracle_results_queue"
request_sqs = "juanmiracle_job_requests"
glacier_sqs = "juanmiracle_glacier_queue"
#[mpcs.aws.sns]
# Change the ARNs below to reflect your SNS topics
job_request_topic = "arn:aws:sns:us-east-1:127134666975:juanmiracle_job_notifications"
job_complete_topic = "arn:aws:sns:us-east-1:127134666975:juanmiracle_results_notifications"
job_glacier_topic = "arn:aws:sns:us-east-1:127134666975:juanmiracle_glacier_notification"

#[mpcs.aws.dynamodb]
# Change the table name to your own
dynamodb_table = "juanmiracle_annotations"

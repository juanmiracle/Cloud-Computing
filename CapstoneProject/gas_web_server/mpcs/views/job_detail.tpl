%include('views/header.tpl')



<div class="container">

    <div class="page-header">
        <h2>Annotation Details</h2>
    </div>

    <div>
        <strong>Request ID:</strong> {{job['job_id']}}<br/>
        <strong>Request Time:</strong> {{job['submit_time']}}<br/>
        <strong>VCF Input File:</strong> {{job['input_file_name']}}<br/>

        % # set row color according to job_status
        % color = 'yellow'
        % color = 'red' if job['job_status']=="FAILED" else color
        % color = 'green' if job['job_status']=="COMPLETED" else color

        <strong>Job Status:</strong> <my style="color:{{color}};">{{job['job_status']}}</my><br/>
    </div>

    %if job['job_status'] == "COMPLETED" or job['job_status'] == 'ARCHIVED':
        <strong>Complete Time:</strong> {{job['complete_time']}}<br/>
    <hr />
    <div>

        % # check if result file is available
        % if result_url is not None:
        <strong>Annotated Results File:</strong> <a href="{{result_url}}">download</a><br/>
        % elif user.role == 'free_user':
        <strong>Annotated Results File:</strong> <a href="{{get_url('subscribe')}}">upgrade to Premium for download</a><br/>
        % else:
        <strong>Annotated Results File:</strong> No Results File <br/>
        % end

        %if job['job_status'] == "COMPLETED":
        <strong>Annotation Log File:</strong> <a href="/annotations/{{job['job_id']}}/log" id="label">Display</a> <a href="{{log_url}}">Download</a><br/><br/>
        %end
    </div>
    %end
    <hr />
    <a href="{{get_url("annotations_list")}}">back to annotations list</a>

</div> <!-- container -->

%rebase('views/base', title='GAS - Annotation Request Received')
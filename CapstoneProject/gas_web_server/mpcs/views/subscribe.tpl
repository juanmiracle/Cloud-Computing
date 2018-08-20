<!--
subscribe.tpl - Get user's credit card details to send to Stripe service
Copyright (C) 2011-2016 Vas Vasiliadis <vas@uchicago.edu>
University of Chicago
-->

%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
	<div class="page-header">
		<h2>Subscribe</h2>
	</div>

	<p>You are subscribing to the GAS Premium plan. Please enter your credit card details to complete your subscription.</p><br />

    <div class="form-wrapper">
		    <form role="form" action="{{get_url('subscribe')}}" method="post" id="subscribe_form" name="subscribe_submit">

		        <!-- display error msgs -->
                <div class="row" >
                    <my class="payment-errors"></my>
                </div>

		        <div class="row">
			        <div class="form-group col-md-5">
		            	<label for="name">Name on Credit Card</label>
		                <input class="form-control input-lg required" type="text" data-stripe="name"/>
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-5">
		            	<label for="email_address">Credit Card Number</label>
		                <input class="form-control input-lg required" type="text" data-stripe="number"/>
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-4">
			            <label for="name">Credit Card Verification Code </label>
		                <input class="form-control input-lg required" type="text" data-stripe="cvc"/>
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-4">
			            <label for="password">Credit Card Expiration Month</label>
		                <input class="form-control input-lg required" type="text" data-stripe="exp-month"/>
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-4">
		                <label for="password">Credit Card Expiration Year</label>
		                <input class="form-control input-lg required" type="text" data-stripe="exp-year"/>
		            </div>
		        </div>

		        <br />
		        <div class="form-actions">
		            <input id="bill-me" class="btn btn-lg btn-primary" type="submit" value="Subscribe">
		        </div>
		    </form>
	    </div>
</div> <!-- container -->

%rebase('views/base', title='GAS - Subscribe')
<!--
register_confirm.tpl - Confirms new user registration request was received
Copyright (C) 2011-2016 Vas Vasiliadis <vas@uchicago.edu>
University of Chicago
-->

%include('views/header.tpl')

<div class="container">
	<div class="page-header">
  	<h2>Registration Confirmed</h2>
  </div>
  <div class="row">
      <p>Thank you for registering! Please <a href="/login">click here</a> to login and start using the GAS.</p>
  </div>
</div> <!-- container -->

%rebase('views/base', title='GAS - Registration Confirmed')
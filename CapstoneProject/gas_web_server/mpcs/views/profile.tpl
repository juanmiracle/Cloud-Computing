%include('views/header.tpl')

<div class="container">

  <div class="page-header">
    <h2>My Account</h2>
  </div>

  <p>
    <strong>Username</strong>: {{user.username}}<br />
    <strong>Name</strong>: {{user.description}}<br />
    <strong>E-mail</strong>: {{user.email_addr}}
  </p>
  <p><strong>Current Plan</strong>: 
      % if (auth.current_user.role == 'free_user'): 
      Free &middot; <a href="/subscribe">Ugrade to Premium plan</a>
      % else: 
      <strong> A Valued Premium User</strong>
  </p>
  %end

</div> 

%rebase('views/base', title='GAS - Annotate')
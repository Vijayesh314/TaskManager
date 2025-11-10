// firebase-auth.js

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
    const idToken = await userCredential.user.getIdToken(/* forceRefresh */ true);

    // Send idToken to server to create session cookie (recommended)
    const resp = await fetch('/sessionLogin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idToken })
    });

    if (!resp.ok) {
      const txt = await resp.text();
      alert("Login failed: " + txt);
      return;
    }

    // Redirect to home/tasks
    window.location = '/';
  } catch (err) {
    console.error(err);
    alert(err.message || "Authentication error");
  }
});

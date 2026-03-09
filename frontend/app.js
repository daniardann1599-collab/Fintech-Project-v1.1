const output = document.getElementById("output");

function show(data) {
  output.textContent = JSON.stringify(data, null, 2);
}

document.getElementById("check-health").addEventListener("click", async () => {
  try {
    const response = await fetch("http://localhost:8000/health");
    show(await response.json());
  } catch (error) {
    show({ error: String(error) });
  }
});

document.getElementById("register").addEventListener("click", async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const response = await fetch("http://localhost:8000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role: "CUSTOMER" })
    });
    const data = await response.json();
    show({ status: response.status, data });
  } catch (error) {
    show({ error: String(error) });
  }
});

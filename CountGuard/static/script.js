function updateCount() {
    fetch('/count')
        .then(res => res.json())
        .then(data => {

            document.getElementById("people-count").innerText = data.count;

            let statusBox = document.getElementById("status");

            if (data.status === "EXCEEDED") {
                statusBox.innerText = "🚨 THRESHOLD EXCEEDED!";
                statusBox.className = "danger";
            } else {
                statusBox.innerText = "✅ STATUS: NORMAL";
                statusBox.className = "normal";
            }

            document.getElementById("email").innerText =
                "Email Alert: " + data.email;
        })
        .catch(err => console.log("Error:", err));
}

setInterval(updateCount, 1000);

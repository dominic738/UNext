document.getElementById("studentForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const studentData = {
        // ---- Financial ----
        target_net_price: Number(document.getElementById("target_net_price").value),
        max_work_hours: Number(document.getElementById("max_work_hours").value),
        family_income: Number(document.getElementById("family_income").value),

        // ---- Importance sliders ----
        importance_afford: Number(document.getElementById("importance_afford").value),
        importance_outcomes: Number(document.getElementById("importance_outcomes").value),
        importance_diversity: Number(document.getElementById("importance_diversity").value),
        importance_mobility: Number(document.getElementById("importance_mobility").value),
        importance_location: Number(document.getElementById("importance_location").value),

        // ---- Academic ----
        sat_score: Number(document.getElementById("sat_score").value) || null,
        act_score: Number(document.getElementById("act_score").value) || null,
        intended_major: document.getElementById("intended_major").value.toLowerCase(),

        // ---- Background ----
        self_ethnicity: document.getElementById("self_ethnicity").value,
        will_work_job: document.getElementById("will_work_job").value === "true",

        // ---- Location ----
        home_lat: Number(document.getElementById("home_lat").value),
        home_lon: Number(document.getElementById("home_lon").value),

        // ---- College preferences ----
        pref_sector: document.getElementById("pref_sector").value || null,
        pref_size: document.getElementById("pref_size").value || null,
    };

    console.log("Sending student profile:", studentData);

    // Send to backend
    const response = await fetch("http://127.0.0.1:8000/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(studentData)
    });

    if (!response.ok) {
        alert("Error from backend: " + response.statusText);
        return;
    }

    const results = await response.json();
    console.log("Received:", results);

    // Store and redirect
    localStorage.setItem("recommendations", JSON.stringify(results));
    window.location.href = "results.html";
});

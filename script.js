console.log("Script loaded on:", window.location.pathname);

/* ------------------------------------------------
   FORM PAGE LOGIC (index.html)
--------------------------------------------------*/
if (window.location.pathname.includes("index.html") || window.location.pathname === "/") {

        // Init Map (center on USA)
    var map = L.map('map').setView([37.8, -96], 4);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18
    }).addTo(map);

    var marker;

    // On map click --> set marker + lat/lon
    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(5);
        const lon = e.latlng.lng.toFixed(5);

        document.getElementById("home_lat").value = lat;
        document.getElementById("home_lon").value = lon;

        if (marker) map.removeLayer(marker);
        marker = L.marker(e.latlng).addTo(map);
    });
    
    document.getElementById("studentForm").addEventListener("submit", async (e) => {
        e.preventDefault();

        // Show spinner
        document.getElementById("loading-overlay").style.display = "flex";

        const studentData = {
            target_net_price: Number(document.getElementById("target_net_price").value),
            max_work_hours: Number(document.getElementById("max_work_hours").value),
            family_income: Number(document.getElementById("family_income").value),

            importance_afford: Number(document.getElementById("importance_afford").value),
            importance_outcomes: Number(document.getElementById("importance_outcomes").value),
            importance_diversity: Number(document.getElementById("importance_diversity").value),
            importance_mobility: Number(document.getElementById("importance_mobility").value),
            importance_location: Number(document.getElementById("importance_location").value),

            sat_score: Number(document.getElementById("sat_score").value) || null,
            act_score: Number(document.getElementById("act_score").value) || null,
            intended_major: document.getElementById("intended_major").value.toLowerCase(),

            self_race: document.getElementById("self_race").value,
            will_work_job: document.getElementById("will_work_job").value === "true",

            home_lat: Number(document.getElementById("home_lat").value),
            home_lon: Number(document.getElementById("home_lon").value),

            pref_sector: document.getElementById("pref_sector").value || null,
            pref_size: document.getElementById("pref_size").value || null,
        };

        console.log("Sending student profile:", studentData);

        try {
            const response = await fetch("http://127.0.0.1:8000/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(studentData)
            });

            if (!response.ok) {
                alert("Backend error: " + response.statusText);
                return;
            }

            const results = await response.json();
            console.log("Received:", results);

            // Save results
            localStorage.setItem("recommendations", JSON.stringify(results));

            // Redirect
            window.location.href = "results.html";

        } catch (error) {
            alert("Network error: " + error.message);

        } finally {
            document.getElementById("loading-overlay").style.display = "none";
        }
    });
}


/* ------------------------------------------------
   RESULTS PAGE LOGIC (results.html)
--------------------------------------------------*/
if (window.location.pathname.includes("results.html")) {

    const resultsDiv = document.getElementById("results");
    const modal = document.getElementById("modal");
    const modalTitle = document.getElementById("modal-title");
    const modalText = document.getElementById("modal-text");
    const closeBtn = document.getElementById("close-btn");

    const stored = JSON.parse(localStorage.getItem("recommendations"));
    console.log("Loaded stored results:", stored);

    if (!stored || stored.length === 0) {
        resultsDiv.innerHTML = "<p>No recommendations found.</p>";
    } else {
        stored.forEach(school => {
            const card = document.createElement("div");
            card.className = "school-card";
            

            card.innerHTML = `
                <h3 class="school-title">${school["Institution Name"]}</h3>
                <p class="school-info"><strong>Match Score:</strong> ${school.match_score.toFixed(1)}</p>
                <p class="school-info"><strong>Net Price:</strong> $${school["Net Price"]}</p>
                <p class="school-info"><strong>Distance:</strong> ${school.distance_km.toFixed(1)} km</p>
                <button class="btn-info">Why this school?</button>
            `;

            card.querySelector(".btn-info").addEventListener("click", () => {
                modalTitle.textContent = school["Institution Name"];
                modalText.textContent = school.rationale;
                modal.style.display = "flex";
            });

            resultsDiv.appendChild(card);

            launchConfetti();
        });
    }

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    window.addEventListener("click", (e) => {
        if (e.target === modal) modal.style.display = "none";
    });
}

function launchConfetti() {
    const duration = 1200; // 1.2 seconds
    const end = Date.now() + duration;

    (function frame() {
        confetti({
            particleCount: 5,
            angle: 60,
            spread: 55,
            origin: { x: 0 }
        });

        confetti({
            particleCount: 5,
            angle: 120,
            spread: 55,
            origin: { x: 1 }
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    })();
}

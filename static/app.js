document.addEventListener("DOMContentLoaded", () => {
    const questionInput = document.getElementById("question");
    const askBtn = document.getElementById("askBtn");
    const answerBox = document.getElementById("answer");
    const loading = document.getElementById("loading");

    const sqlBox = document.getElementById("sqlBox");
    const tableHead = document.getElementById("tableHead");
    const tableBody = document.getElementById("tableBody");

    const voiceBtn = document.getElementById("voiceBtn");
    const languageSelect = document.getElementById("languageSelect");

    let voices = [];

    // =========================================
    // Load Voices
    // =========================================
    function loadVoices() {
        voices = window.speechSynthesis.getVoices();
        console.log("Available Voices:", voices);
    }

    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;

    // =========================================
    // Sample Questions
    // =========================================
    document.querySelectorAll(".sample-question").forEach(button => {
        button.addEventListener("click", () => {
            questionInput.value = button.innerText;
        });
    });

    // =========================================
    // Ask Button
    // =========================================
    if (askBtn) {
        askBtn.addEventListener("click", askQuestion);
    }

    // =========================================
    // Enter Key
    // =========================================
    if (questionInput) {
        questionInput.addEventListener("keypress", e => {
            if (e.key === "Enter") {
                askQuestion();
            }
        });
    }

    // =========================================
    // Voice Recognition
    // =========================================
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition && voiceBtn) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        voiceBtn.addEventListener("click", () => {
            recognition.lang = languageSelect?.value || "en-US";
            voiceBtn.classList.add("listening");
            recognition.start();
        });

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            questionInput.value = transcript;
            askQuestion();
        };

        recognition.onend = function () {
            voiceBtn.classList.remove("listening");
        };

        recognition.onerror = function (e) {
            console.error(e);
            voiceBtn.classList.remove("listening");
            alert("Voice recognition failed");
        };
    }

    // =========================================
    // Ask Question
    // =========================================
    async function askQuestion() {
        const question = questionInput.value.trim();

        if (!question) {
            alert("Please enter a question");
            return;
        }

        resetUI();

        if (loading) loading.classList.remove("d-none");

        if (askBtn) {
            askBtn.disabled = true;
            askBtn.innerText = "Thinking...";
        }

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question })
            });

            if (!response.ok) {
                throw new Error("Server Error");
            }

            const data = await response.json();

            const answer = data.answer || "No response";

            typeAnswer(answer);
            speakAnswer(answer);

            displaySQL(data.sql || "");
            displayTable(data.rows || []);

        } catch (error) {
            console.error(error);

            if (answerBox) {
                answerBox.innerHTML = `
                    <div class="error">
                        Failed to connect to server.
                    </div>
                `;
            }
        } finally {
            if (loading) loading.classList.add("d-none");

            if (askBtn) {
                askBtn.disabled = false;
                askBtn.innerText = "Ask AI";
            }
        }
    }

    // =========================================
    // Speak Answer
    // =========================================
    function speakAnswer(text) {
        if (!window.speechSynthesis) {
            console.log("Speech not supported");
            return;
        }

        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        const lang = languageSelect?.value || "en-US";

        utterance.lang = lang;
        utterance.rate = 0.95;
        utterance.pitch = 1;
        utterance.volume = 1;

        let selectedVoice = null;

        if (lang === "ta-IN") {
            selectedVoice = voices.find(v =>
                v.lang.includes("ta") || v.name.toLowerCase().includes("tamil")
            );
        } else if (lang === "hi-IN") {
            selectedVoice = voices.find(v =>
                v.lang.includes("hi") || v.name.toLowerCase().includes("hindi")
            );
        } else {
            selectedVoice = voices.find(v =>
                v.lang.includes("en")
            );
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
            console.log("Using voice:", selectedVoice.name);
        } else {
            console.log("No matching voice found. Browser default used.");
        }

        setTimeout(() => {
            speechSynthesis.speak(utterance);
        }, 200);
    }

    // =========================================
    // Reset UI
    // =========================================
    function resetUI() {
        if (answerBox) {
            answerBox.innerHTML = "Analyzing your business data...";
        }

        if (sqlBox) sqlBox.textContent = "";
        if (tableHead) tableHead.innerHTML = "";
        if (tableBody) tableBody.innerHTML = "";
    }

    // =========================================
    // Typing Effect
    // =========================================
    function typeAnswer(text) {
        if (!answerBox) return;

        answerBox.innerHTML = "";
        let i = 0;

        function type() {
            if (i < text.length) {
                answerBox.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, 15);
            }
        }

        type();
    }

    // =========================================
    // SQL Display
    // =========================================
    function displaySQL(sql) {
        if (sqlBox) {
            sqlBox.textContent = sql;
        }
    }

    // =========================================
    // Table Display
    // =========================================
    function displayTable(rows) {
        if (!tableHead || !tableBody) return;

        tableHead.innerHTML = "";
        tableBody.innerHTML = "";

        if (!rows || rows.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="20">No Records Found</td>
                </tr>
            `;
            return;
        }

        const headers = Object.keys(rows[0]);

        headers.forEach(header => {
            const th = document.createElement("th");
            th.innerText = header;
            tableHead.appendChild(th);
        });

        rows.forEach(row => {
            const tr = document.createElement("tr");

            headers.forEach(header => {
                const td = document.createElement("td");
                let value = row[header];

                if (value === null || value === undefined) {
                    value = "";
                }

                td.innerText = value;
                tr.appendChild(td);
            });

            tableBody.appendChild(tr);
        });
    }
});
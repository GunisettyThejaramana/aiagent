// =====================================================
// Enterprise AI Assistant
// app.js
// Part 1
// =====================================================

document.addEventListener("DOMContentLoaded", () => {

    const questionInput = document.getElementById("question");
    const askBtn = document.getElementById("askBtn");

    const answerBox = document.getElementById("answer");
    const sqlBox = document.getElementById("sqlBox");

    const tableHead = document.getElementById("tableHead");
    const tableBody = document.getElementById("tableBody");

    const loading = document.getElementById("loading");

    //--------------------------------------------------
    // Sample Questions
    //--------------------------------------------------

    document.querySelectorAll(".sample-question").forEach(button => {

        button.addEventListener("click", () => {

            questionInput.value = button.innerText;

        });

    });

    //--------------------------------------------------
    // Ask Button
    //--------------------------------------------------

    askBtn.addEventListener("click", () => {

        askQuestion();

    });

    //--------------------------------------------------
    // Press Enter
    //--------------------------------------------------

    questionInput.addEventListener("keypress", function (e) {

        if (e.key === "Enter") {

            askQuestion();

        }

    });

    //--------------------------------------------------
    // Main Function
    //--------------------------------------------------

    async function askQuestion() {

        const question = questionInput.value.trim();

        if (question === "") {

            alert("Please enter a question.");

            return;

        }

        loading.classList.remove("d-none");

        answerBox.innerHTML = "";

        sqlBox.innerHTML = "";

        tableHead.innerHTML = "";

        tableBody.innerHTML = "";

        askBtn.disabled = true;

        try {

            const response = await fetch("/ask", {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    question: question

                })

            });

            if (!response.ok) {

                throw new Error("Server Error");

            }

            const data = await response.json();

            displayAnswer(data);

            displaySQL(data);

            displayTable(data.rows);

        }

        catch (error) {

            console.error(error);

            answerBox.innerHTML =

                `<div class="error">

                    Failed to connect to server.

                 </div>`;

        }

        finally {

            loading.classList.add("d-none");

            askBtn.disabled = false;

        }

    }

    //--------------------------------------------------
    // Display AI Answer
    //--------------------------------------------------

    function displayAnswer(data) {

        answerBox.classList.add("fade-in");

        answerBox.innerHTML =

            `<div class="success">

                ${data.answer}

            </div>`;

    }

    //--------------------------------------------------
    // Display SQL
    //--------------------------------------------------

    function displaySQL(data) {

        sqlBox.textContent = data.sql;

    }

    //--------------------------------------------------
    // Display Table
    //--------------------------------------------------

    function displayTable(rows) {

        if (!rows || rows.length === 0) {

            tableBody.innerHTML =

                `<tr>

                    <td colspan="20">

                        No Records Found

                    </td>

                </tr>`;

            return;

        }

        //--------------------------------------------------
        // Create Header
        //--------------------------------------------------

        const headers = Object.keys(rows[0]);

        headers.forEach(header => {

            const th = document.createElement("th");

            th.innerText = header;

            tableHead.appendChild(th);

        });

        //--------------------------------------------------
        // Create Rows
        //--------------------------------------------------

        rows.forEach(row => {

            const tr = document.createElement("tr");

                        headers.forEach(header => {

                const td = document.createElement("td");

                let value = row[header];

                // Handle null/undefined values
                if (value === null || value === undefined) {
                    value = "";
                }

                // Format numbers
                if (typeof value === "number") {

                    if (Number.isInteger(value)) {
                        value = value.toLocaleString();
                    } else {
                        value = value.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                    }
                }

                // Format dates
                if (
                    typeof value === "string" &&
                    /^\d{4}-\d{2}-\d{2}/.test(value)
                ) {
                    const date = new Date(value);

                    if (!isNaN(date)) {
                        value = date.toLocaleDateString();
                    }
                }

                td.innerText = value;

                tr.appendChild(td);

            });

            tableBody.appendChild(tr);

        });

        // Scroll to answer
        answerBox.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }

});
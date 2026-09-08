
document.addEventListener("DOMContentLoaded", () => {

    /* =========================================================
       ELEMENTS
    ========================================================== */

    const questionInput =
        document.getElementById("question");

    const askBtn =
        document.getElementById("askBtn");

    const answerBox =
        document.getElementById("answer");

    const loading =
        document.getElementById("loading");

    const sqlBox =
        document.getElementById("sqlBox");

    const sqlSection =
        document.getElementById("sqlSection");

    const tableHead =
        document.getElementById("tableHead");

    const tableBody =
        document.getElementById("tableBody");

    const tableSection =
        document.getElementById("tableSection");

    const voiceBtn =
        document.getElementById("voiceBtn");

    const inlineVoiceBtn =
        document.getElementById("inlineVoiceBtn");

    const languageSelect =
        document.getElementById("languageSelect");

    const voiceStatus =
        document.getElementById("voiceStatus");

    const databaseList =
        document.getElementById("databaseList");

    const selectedDatabaseName =
        document.getElementById("selectedDatabaseName");

    const detailDatabaseName =
        document.getElementById("detailDatabaseName");

    const detailDatabaseType =
        document.getElementById("detailDatabaseType");

    const detailHost =
        document.getElementById("detailHost");

    const detailPort =
        document.getElementById("detailPort");

    const detailDatabase =
        document.getElementById("detailDatabase");

    const detailUsername =
        document.getElementById("detailUsername");

    const detailDatabaseLogo =
        document.querySelector(".large-db-logo");


    /* =========================================================
       DATABASE STATE
    ========================================================== */

    let databases = [];

    let selectedDatabase = null;

    let selectedDatabaseType = "PostgreSQL";


    /* =========================================================
       AUTH HEADERS
    ========================================================== */

    function getHeaders() {

        const headers = {
            "Content-Type": "application/json"
        };

        const token =
            localStorage.getItem("token");

        if (token) {

            headers["Authorization"] =
                `Bearer ${token}`;

        }

        return headers;
    }


    /* =========================================================
       DATABASE ICON
    ========================================================== */

    function getDatabaseLogoClass(type) {

        const normalized =
            String(type || "")
                .toLowerCase();

        if (normalized.includes("postgres")) {
            return "postgres-logo";
        }

        if (normalized.includes("mysql")) {
            return "mysql-logo";
        }

        if (
            normalized.includes("sql server") ||
            normalized.includes("sqlserver")
        ) {
            return "sqlserver-logo";
        }

        if (normalized.includes("oracle")) {
            return "oracle-logo";
        }

        if (normalized.includes("sqlite")) {
            return "sqlite-logo";
        }

        return "postgres-logo";
    }


    /* =========================================================
       DATABASE DISPLAY DATA
    ========================================================== */

    function normalizeDatabase(database) {

        return {
            id: database.id,
            name: database.name,
            type: database.db_type,
            host: database.host,
            port: database.port,
            database: database.database_name,
            username: database.username
        };

    }


    /* =========================================================
       UPDATE SELECTED DATABASE DETAILS
    ========================================================== */

    function updateDatabaseDetails() {

        if (!selectedDatabase) {

            if (selectedDatabaseName) {
                selectedDatabaseName.innerText =
                    "No database selected";
            }

            if (detailDatabaseName) {
                detailDatabaseName.innerText =
                    "No database selected";
            }

            if (detailDatabaseType) {
                detailDatabaseType.innerText =
                    "—";
            }

            if (detailHost) {
                detailHost.innerText =
                    "—";
            }

            if (detailPort) {
                detailPort.innerText =
                    "—";
            }

            if (detailDatabase) {
                detailDatabase.innerText =
                    "—";
            }

            if (detailUsername) {
                detailUsername.innerText =
                    "—";
            }

            if (questionInput) {
                questionInput.placeholder =
                    "Select a database and ask a question...";
            }

            return;
        }


        if (selectedDatabaseName) {

            selectedDatabaseName.innerText =
                selectedDatabase.name;

        }


        if (detailDatabaseName) {

            detailDatabaseName.innerText =
                selectedDatabase.name;

        }


        if (detailDatabaseType) {

            detailDatabaseType.innerText =
                selectedDatabase.type;

        }


        if (detailHost) {

            detailHost.innerText =
                selectedDatabase.host || "—";

        }


        if (detailPort) {

            detailPort.innerText =
                selectedDatabase.port || "—";

        }


        if (detailDatabase) {

            detailDatabase.innerText =
                selectedDatabase.database || "—";

        }


        if (detailUsername) {

            detailUsername.innerText =
                selectedDatabase.username || "—";

        }


        if (questionInput) {

            questionInput.placeholder =
                `Ask anything about ${selectedDatabase.name}...`;

        }


        if (detailDatabaseLogo) {

            detailDatabaseLogo.classList.remove(
                "postgres-logo",
                "mysql-logo",
                "sqlserver-logo",
                "oracle-logo",
                "sqlite-logo"
            );

            detailDatabaseLogo.classList.add(
                getDatabaseLogoClass(
                    selectedDatabase.type
                )
            );

        }

    }


    /* =========================================================
       SELECT DATABASE
    ========================================================== */

    function selectDatabase(database) {

        if (!database) {
            return;
        }

        selectedDatabase = database;

        document
            .querySelectorAll(".database-item")
            .forEach(item => {

                item.classList.remove(
                    "selected"
                );

                if (
                    String(item.dataset.dbId) ===
                    String(database.id)
                ) {

                    item.classList.add(
                        "selected"
                    );

                }

            });

        updateDatabaseDetails();

        console.log(
            "Selected database:",
            selectedDatabase
        );

    }


    /* =========================================================
       RENDER DATABASE LIST
    ========================================================== */

    function renderDatabases() {

        if (!databaseList) {
            return;
        }

        databaseList.innerHTML = "";


        if (
            !databases ||
            databases.length === 0
        ) {

            databaseList.innerHTML = `
                <div class="database-empty">
                    <i class="bi bi-database"></i>
                    <strong>No databases connected</strong>
                    <span>Click "Add Database" to connect one.</span>
                </div>
            `;

            selectedDatabase = null;

            updateDatabaseDetails();

            return;
        }


        databases.forEach(database => {

            const item =
                document.createElement("div");

            item.className =
                "database-item";


            const logoClass =
                getDatabaseLogoClass(
                    database.type
                );


            item.dataset.dbId =
                database.id;

            item.dataset.dbName =
                database.name;

            item.dataset.dbType =
                database.type || "";

            item.dataset.dbHost =
                database.host || "";

            item.dataset.dbPort =
                database.port || "";

            item.dataset.dbDatabase =
                database.database || "";

            item.dataset.dbUsername =
                database.username || "";


            item.innerHTML = `

                <div class="database-logo ${logoClass}">
                    <i class="bi bi-database-fill"></i>
                </div>

                <div class="database-info">

                    <strong>
                        ${escapeHtml(database.name)}
                    </strong>

                    <span>
                        ${escapeHtml(database.type || "Database")}
                    </span>

                </div>

                <div class="database-status connected">
                    <span></span>
                    Connected
                </div>

                <button
                    type="button"
                    class="more-button"
                    title="Database options"
                >
                    <i class="bi bi-three-dots"></i>
                </button>

            `;


            item.addEventListener(
                "click",
                event => {

                    if (
                        event.target.closest(
                            ".more-button"
                        )
                    ) {
                        return;
                    }

                    selectDatabase(database);

                }
            );


            databaseList.appendChild(item);

        });


        /*
         * Restore the previously selected database
         * if it still exists.
         */

        if (selectedDatabase) {

            const existing =
                databases.find(
                    database =>
                        String(database.id) ===
                        String(selectedDatabase.id)
                );

            if (existing) {

                selectDatabase(
                    existing
                );

                return;
            }

        }


        /*
         * Otherwise select the first database.
         */

        selectDatabase(
            databases[0]
        );

    }


    /* =========================================================
       LOAD DATABASES FROM BACKEND
    ========================================================== */

    async function loadDatabases() {

        if (databaseList) {

            databaseList.innerHTML = `
                <div class="database-empty">
                    <div class="spinner-border spinner-border-sm"></div>
                    <span>Loading databases...</span>
                </div>
            `;

        }


        try {

            const response =
                await fetch(
                    "/api/databases",
                    {
                        method: "GET",
                        headers: getHeaders()
                    }
                );


            if (!response.ok) {

                let message =
                    "Unable to load databases.";

                try {

                    const errorData =
                        await response.json();

                    message =
                        errorData.detail ||
                        message;

                } catch (_) {}

                throw new Error(
                    message
                );

            }


            const data =
                await response.json();


            databases =
                Array.isArray(data)
                    ? data.map(
                        normalizeDatabase
                    )
                    : [];


            console.log(
                "Loaded databases:",
                databases
            );


            renderDatabases();


        } catch (error) {

            console.error(
                "Database loading error:",
                error
            );


            if (databaseList) {

                databaseList.innerHTML = `
                    <div class="database-empty">
                        <i class="bi bi-exclamation-triangle"></i>
                        <strong>Unable to load databases</strong>
                        <span>
                            ${escapeHtml(error.message)}
                        </span>
                    </div>
                `;

            }

        }

    }


    /* =========================================================
       INITIAL DATABASE LOAD
    ========================================================== */

    loadDatabases();


    /* =========================================================
       VOICES
    ========================================================== */

    let voices = [];


    function loadVoices() {

        if (!window.speechSynthesis) {
            return;
        }

        voices =
            window.speechSynthesis.getVoices();

        console.log(
            "Available Voices:",
            voices
        );

    }


    loadVoices();


    if (window.speechSynthesis) {

        window.speechSynthesis.onvoiceschanged =
            loadVoices;

    }


    /* =========================================================
       SAMPLE QUESTIONS
    ========================================================== */

    document
        .querySelectorAll(".sample-question")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    if (!questionInput) {
                        return;
                    }

                    questionInput.value =
                        button.innerText;

                    questionInput.focus();

                }
            );

        });


    /* =========================================================
       ASK BUTTON
    ========================================================== */

    if (askBtn) {

        askBtn.addEventListener(
            "click",
            askQuestion
        );

    }


    /* =========================================================
       ENTER KEY
    ========================================================== */

    if (questionInput) {

        questionInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    askQuestion();

                }

            }
        );

    }


    /* =========================================================
       SPEECH RECOGNITION
    ========================================================== */

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    let recognition = null;


    if (SpeechRecognition) {

        recognition =
            new SpeechRecognition();

        recognition.continuous = false;

        recognition.interimResults = false;


        function startVoiceRecognition() {

            if (!recognition) {
                return;
            }


            const language =
                languageSelect?.value ||
                "en-US";


            recognition.lang =
                language;


            if (voiceBtn) {

                voiceBtn.classList.add(
                    "listening"
                );

            }


            if (inlineVoiceBtn) {

                inlineVoiceBtn.classList.add(
                    "listening"
                );

            }


            if (voiceStatus) {

                voiceStatus.innerText =
                    "Listening...";

            }


            try {

                recognition.start();

            } catch (error) {

                console.log(
                    "Recognition already running."
                );

            }

        }


        if (voiceBtn) {

            voiceBtn.addEventListener(
                "click",
                startVoiceRecognition
            );

        }


        if (inlineVoiceBtn) {

            inlineVoiceBtn.addEventListener(
                "click",
                startVoiceRecognition
            );

        }


        recognition.onresult =
            event => {

                const transcript =
                    event.results[0][0]
                        .transcript;


                if (questionInput) {

                    questionInput.value =
                        transcript;

                }


                if (voiceStatus) {

                    voiceStatus.innerText =
                        "Question received";

                }


                askQuestion();

            };


        recognition.onend =
            () => {

                if (voiceBtn) {

                    voiceBtn.classList.remove(
                        "listening"
                    );

                }


                if (inlineVoiceBtn) {

                    inlineVoiceBtn.classList.remove(
                        "listening"
                    );

                }


                if (voiceStatus) {

                    voiceStatus.innerText =
                        "Click to speak";

                }

            };


        recognition.onerror =
            error => {

                console.error(
                    "Speech recognition error:",
                    error
                );


                if (voiceBtn) {

                    voiceBtn.classList.remove(
                        "listening"
                    );

                }


                if (inlineVoiceBtn) {

                    inlineVoiceBtn.classList.remove(
                        "listening"
                    );

                }


                if (voiceStatus) {

                    voiceStatus.innerText =
                        "Voice recognition failed";


                    setTimeout(
                        () => {

                            voiceStatus.innerText =
                                "Click to speak";

                        },
                        2500
                    );

                }

            };

    } else {

        if (voiceBtn) {

            voiceBtn.title =
                "Voice recognition is not supported by this browser";

        }

    }


    /* =========================================================
       ASK QUESTION
    ========================================================== */

    async function askQuestion() {

        if (!questionInput) {
            return;
        }


        const question =
            questionInput.value.trim();


        if (!question) {

            showAnswer(
                "Please enter a question."
            );

            questionInput.focus();

            return;

        }


        if (!selectedDatabase) {

            showAnswer(
                "Please select a database first."
            );

            return;

        }


        resetUI();


        if (loading) {

            loading.classList.remove(
                "d-none"
            );

        }


        if (askBtn) {

            askBtn.disabled = true;

            askBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm me-1"></span> Thinking...';

        }


        try {

            /*
             * IMPORTANT:
             *
             * The backend QuestionRequest expects:
             *
             * question
             * language
             * database_id
             *
             * We now send the correct database_id.
             */

            const requestBody = {

                question:
                    question,

                user_id:
                    "default_user",

                language:
                    languageSelect?.value ||
                    "en-US",

                database_id:
                    Number(
                        selectedDatabase.id
                    )

            };


            console.log(
                "Sending AI request:",
                requestBody
            );


            const response =
                await fetch(
                    "/ask",
                    {
                        method: "POST",
                        headers: getHeaders(),
                        body:
                            JSON.stringify(
                                requestBody
                            )
                    }
                );


            if (!response.ok) {

                let errorMessage =
                    "Server Error";


                try {

                    const errorData =
                        await response.json();

                    errorMessage =
                        errorData.detail ||
                        errorMessage;

                } catch (_) {}


                throw new Error(
                    errorMessage
                );

            }


            const data =
                await response.json();


            console.log(
                "AI response:",
                data
            );


            const answer =
                data.answer ||
                "No response received from AI.";


            typeAnswer(
                answer
            );


            speakAnswer(
                answer
            );


            displaySQL(
                data.sql || ""
            );


            displayTable(
                data.rows || []
            );


            addRecentQuery(
                question,
                selectedDatabase.name,
                selectedDatabase.type
            );


        } catch (error) {

            console.error(
                "Ask error:",
                error
            );


            showAnswer(
                `Unable to get an answer.\n\n${error.message}`
            );

        } finally {

            if (loading) {

                loading.classList.add(
                    "d-none"
                );

            }


            if (askBtn) {

                askBtn.disabled = false;

                askBtn.innerHTML =
                    '<i class="bi bi-send-fill"></i>';

            }

        }

    }


    /* =========================================================
       ANSWER
    ========================================================== */

    function showAnswer(text) {

        if (!answerBox) {
            return;
        }

        answerBox.innerText =
            text;

    }


    function typeAnswer(text) {

        if (!answerBox) {
            return;
        }


        answerBox.innerText = "";

        let index = 0;


        function type() {

            if (
                index <
                text.length
            ) {

                answerBox.innerText +=
                    text.charAt(index);

                index++;

                setTimeout(
                    type,
                    10
                );

            }

        }


        type();

    }


    /* =========================================================
       TEXT TO SPEECH
    ========================================================== */

    function speakAnswer(text) {

        if (!window.speechSynthesis) {

            console.log(
                "Speech synthesis not supported."
            );

            return;

        }


        window.speechSynthesis.cancel();


        const utterance =
            new SpeechSynthesisUtterance(
                text
            );


        const language =
            languageSelect?.value ||
            "en-US";


        utterance.lang =
            language;

        utterance.rate =
            0.95;

        utterance.pitch =
            1;

        utterance.volume =
            1;


        let selectedVoice =
            null;


        if (language === "ta-IN") {

            selectedVoice =
                voices.find(
                    voice =>
                        voice.lang
                            .toLowerCase()
                            .includes("ta") ||
                        voice.name
                            .toLowerCase()
                            .includes("tamil")
                );

        } else if (
            language === "hi-IN"
        ) {

            selectedVoice =
                voices.find(
                    voice =>
                        voice.lang
                            .toLowerCase()
                            .includes("hi") ||
                        voice.name
                            .toLowerCase()
                            .includes("hindi")
                );

        } else {

            selectedVoice =
                voices.find(
                    voice =>
                        voice.lang
                            .toLowerCase()
                            .startsWith("en")
                );

        }


        if (selectedVoice) {

            utterance.voice =
                selectedVoice;

        }


        setTimeout(
            () => {

                window.speechSynthesis
                    .speak(
                        utterance
                    );

            },
            200
        );

    }


    /* =========================================================
       RESET UI
    ========================================================== */

    function resetUI() {

        if (answerBox) {

            answerBox.innerText =
                "Analyzing your business data...";

        }


        if (sqlSection) {

            sqlSection.classList.add(
                "d-none"
            );

        }


        if (tableSection) {

            tableSection.classList.add(
                "d-none"
            );

        }


        if (sqlBox) {

            sqlBox.textContent = "";

        }


        if (tableHead) {

            tableHead.innerHTML = "";

        }


        if (tableBody) {

            tableBody.innerHTML = "";

        }

    }


    /* =========================================================
       DISPLAY SQL
    ========================================================== */

    function displaySQL(sql) {

        if (
            !sqlSection ||
            !sqlBox
        ) {
            return;
        }


        if (!sql) {

            sqlSection.classList.add(
                "d-none"
            );

            return;

        }


        sqlBox.textContent =
            sql;


        sqlSection.classList.remove(
            "d-none"
        );

    }


    /* =========================================================
       DISPLAY TABLE
    ========================================================== */

    function displayTable(rows) {

        if (
            !tableHead ||
            !tableBody ||
            !tableSection
        ) {

            return;

        }


        tableHead.innerHTML = "";

        tableBody.innerHTML = "";


        if (
            !rows ||
            rows.length === 0
        ) {

            tableSection.classList.add(
                "d-none"
            );

            return;

        }


        const headers =
            Object.keys(
                rows[0]
            );


        headers.forEach(
            header => {

                const th =
                    document.createElement(
                        "th"
                    );


                th.innerText =
                    header;


                tableHead.appendChild(
                    th
                );

            }
        );


        rows.forEach(
            row => {

                const tr =
                    document.createElement(
                        "tr"
                    );


                headers.forEach(
                    header => {

                        const td =
                            document.createElement(
                                "td"
                            );


                        let value =
                            row[header];


                        if (
                            value === null ||
                            value === undefined
                        ) {

                            value = "";

                        }


                        td.innerText =
                            value;


                        tr.appendChild(
                            td
                        );

                    }
                );


                tableBody.appendChild(
                    tr
                );

            }
        );


        tableSection.classList.remove(
            "d-none"
        );

    }


    /* =========================================================
       RECENT QUERY
    ========================================================== */

    function addRecentQuery(
        question,
        databaseName,
        databaseType
    ) {

        const recentList =
            document.getElementById(
                "recentQueries"
            );


        if (!recentList) {
            return;
        }


        const item =
            document.createElement(
                "div"
            );


        item.className =
            "recent-item";


        const logoClass =
            getDatabaseLogoClass(
                databaseType
            );


        item.innerHTML = `

            <div class="recent-db-icon ${logoClass}">
                <i class="bi bi-database-fill"></i>
            </div>

            <div class="recent-content">

                <strong>
                    ${escapeHtml(question)}
                </strong>

                <span>
                    <i class="bi bi-database-fill"></i>
                    ${escapeHtml(databaseName)}
                </span>

            </div>

            <time>
                Just now
            </time>

        `;


        recentList.prepend(
            item
        );


        while (
            recentList.children.length >
            5
        ) {

            recentList.removeChild(
                recentList.lastElementChild
            );

        }

    }


    /* =========================================================
       HTML ESCAPE
    ========================================================== */

    function escapeHtml(value) {

        return String(value)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );

    }


    /* =========================================================
       ADD DATABASE MODAL
    ========================================================== */

    const databaseModalElement =
        document.getElementById(
            "databaseModal"
        );


    let databaseModal = null;


    if (
        databaseModalElement &&
        window.bootstrap
    ) {

        databaseModal =
            new bootstrap.Modal(
                databaseModalElement
            );

    }


    const addDatabaseBtn =
        document.getElementById(
            "addDatabaseBtn"
        );


    const quickNewConnection =
        document.getElementById(
            "quickNewConnection"
        );


    function openDatabaseModal() {

        if (databaseModal) {

            databaseModal.show();

        }

    }


    if (addDatabaseBtn) {

        addDatabaseBtn.addEventListener(
            "click",
            openDatabaseModal
        );

    }


    if (quickNewConnection) {

        quickNewConnection.addEventListener(
            "click",
            openDatabaseModal
        );

    }


    /* =========================================================
       DATABASE TYPE
    ========================================================== */

    document
        .querySelectorAll(
            ".database-type"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    document
                        .querySelectorAll(
                            ".database-type"
                        )
                        .forEach(
                            item =>
                                item.classList.remove(
                                    "selected"
                                )
                        );


                    button.classList.add(
                        "selected"
                    );


                    selectedDatabaseType =
                        button.dataset.type;


                    updateDefaultPort();

                }
            );

        });


    function updateDefaultPort() {

        const portInput =
            document.getElementById(
                "connectionPort"
            );


        if (!portInput) {
            return;
        }


        const ports = {

            "PostgreSQL":
                "5432",

            "MySQL":
                "3306",

            "SQL Server":
                "1433",

            "Oracle":
                "1521"

        };


        portInput.value =
            ports[
                selectedDatabaseType
            ] || "";

    }


    /* =========================================================
       PASSWORD TOGGLE
    ========================================================== */

    const togglePassword =
        document.getElementById(
            "togglePassword"
        );


    const passwordInput =
        document.getElementById(
            "connectionPassword"
        );


    if (
        togglePassword &&
        passwordInput
    ) {

        togglePassword.addEventListener(
            "click",
            () => {

                const isPassword =
                    passwordInput.type ===
                    "password";


                passwordInput.type =
                    isPassword
                        ? "text"
                        : "password";


                togglePassword.innerHTML =
                    isPassword
                        ? '<i class="bi bi-eye-slash"></i>'
                        : '<i class="bi bi-eye"></i>';

            }
        );

    }


    /* =========================================================
       TEST CONNECTION
    ========================================================== */

    const testConnectionBtn =
        document.getElementById(
            "testConnectionBtn"
        );


    const connectionMessage =
        document.getElementById(
            "connectionMessage"
        );


    if (testConnectionBtn) {

        testConnectionBtn.addEventListener(
            "click",
            async () => {

                const host =
                    document.getElementById(
                        "connectionHost"
                    )?.value.trim();


                const port =
                    document.getElementById(
                        "connectionPort"
                    )?.value.trim();


                const database =
                    document.getElementById(
                        "connectionDatabase"
                    )?.value.trim();


                const username =
                    document.getElementById(
                        "connectionUsername"
                    )?.value.trim();


                const password =
                    document.getElementById(
                        "connectionPassword"
                    )?.value;


                if (
                    !host ||
                    !port ||
                    !database ||
                    !username ||
                    !password
                ) {

                    showConnectionMessage(
                        "Please fill all connection details.",
                        "error"
                    );

                    return;

                }


                /*
                 * Backend schema uses:
                 *
                 * db_type
                 * database_name
                 */

                testConnectionBtn.disabled =
                    true;


                testConnectionBtn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-1"></span> Testing...';


                try {

                    const response =
                        await fetch(
                            "/api/databases/test",
                            {
                                method: "POST",

                                headers:
                                    getHeaders(),

                                body: JSON.stringify({

    db_type: selectedDatabaseType
        .toLowerCase()
        .replace(/\s+/g, ""),

    host: host,

    port: Number(port),

    database_name: database,

    username: username,

    password: password
})

                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            data.message ||
                            "Connection test failed."
                        );

                    }


                    if (
                        data.success
                    ) {

                        showConnectionMessage(
                            data.message ||
                            "Database connection successful.",
                            "success"
                        );

                    } else {

                        showConnectionMessage(
                            data.message ||
                            "Database connection failed.",
                            "error"
                        );

                    }


                } catch (error) {

                    console.error(
                        "Connection test error:",
                        error
                    );


                    showConnectionMessage(
                        error.message ||
                        "Unable to test connection.",
                        "error"
                    );

                } finally {

                    testConnectionBtn.disabled =
                        false;

                    testConnectionBtn.innerHTML =
                        '<i class="bi bi-plug"></i> Test Connection';

                }

            }
        );

    }


    function showConnectionMessage(
        message,
        type
    ) {

        if (!connectionMessage) {
            return;
        }


        connectionMessage.className =
            `connection-message ${type}`;


        connectionMessage.innerText =
            message;

    }


    /* =========================================================
       SAVE DATABASE
    ========================================================== */

    const saveDatabaseBtn =
        document.getElementById(
            "saveDatabaseBtn"
        );


    if (saveDatabaseBtn) {

        saveDatabaseBtn.addEventListener(
            "click",
            async () => {

                const connectionName =
                    document.getElementById(
                        "connectionName"
                    )?.value.trim();


                const host =
                    document.getElementById(
                        "connectionHost"
                    )?.value.trim();


                const port =
                    document.getElementById(
                        "connectionPort"
                    )?.value.trim();


                const database =
                    document.getElementById(
                        "connectionDatabase"
                    )?.value.trim();


                const username =
                    document.getElementById(
                        "connectionUsername"
                    )?.value.trim();


                const password =
                    document.getElementById(
                        "connectionPassword"
                    )?.value;


                if (
                    !connectionName ||
                    !host ||
                    !port ||
                    !database ||
                    !username ||
                    !password
                ) {

                    showConnectionMessage(
                        "Please complete all fields before saving.",
                        "error"
                    );

                    return;

                }


                /*
                 * Oracle is displayed in the UI,
                 * but the current backend does not
                 * yet support Oracle.
                 */

                if (
                    selectedDatabaseType ===
                    "Oracle"
                ) {

                    showConnectionMessage(
                        "Oracle support is not enabled in the current backend yet.",
                        "error"
                    );

                    return;

                }


                saveDatabaseBtn.disabled =
                    true;


                saveDatabaseBtn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';


                try {

                    const response =
                        await fetch(
                            "/api/databases",
                            {
                                method: "POST",

                                headers:
                                    getHeaders(),
                                    
                                    body: JSON.stringify({

    name: connectionName,

    db_type: selectedDatabaseType
        .toLowerCase()
        .replace(/\s+/g, ""),

    host: host,

    port: Number(port),

    database_name: database,

    username: username,

    password: password
})

                                
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Unable to save database."
                        );

                    }


                    showConnectionMessage(
                        "Database saved successfully.",
                        "success"
                    );


                    /*
                     * Reload real databases from backend.
                     */

                    await loadDatabases();


                    /*
                     * Select newly created database.
                     */

                    if (data && data.id) {

                        const savedDatabase =
                            databases.find(
                                databaseItem =>
                                    String(
                                        databaseItem.id
                                    ) ===
                                    String(data.id)
                            );

                        if (savedDatabase) {

                            selectDatabase(
                                savedDatabase
                            );

                        }

                    }


                    /*
                     * Clear form.
                     */

                    clearDatabaseForm();


                    setTimeout(
                        () => {

                            if (databaseModal) {

                                databaseModal.hide();

                            }

                        },
                        900
                    );


                } catch (error) {

                    console.error(
                        "Save database error:",
                        error
                    );


                    showConnectionMessage(
                        error.message ||
                        "Unable to save database.",
                        "error"
                    );

                } finally {

                    saveDatabaseBtn.disabled =
                        false;

                    saveDatabaseBtn.innerHTML =
                        '<i class="bi bi-check-lg"></i> Save Database';

                }

            }
        );

    }


    /* =========================================================
       CLEAR DATABASE FORM
    ========================================================== */

    function clearDatabaseForm() {

        const fields = [

            "connectionName",
            "connectionHost",
            "connectionPort",
            "connectionDatabase",
            "connectionUsername",
            "connectionPassword"

        ];


        fields.forEach(
            id => {

                const element =
                    document.getElementById(
                        id
                    );

                if (element) {
                    element.value = "";
                }

            }
        );


        selectedDatabaseType =
            "PostgreSQL";


        document
            .querySelectorAll(
                ".database-type"
            )
            .forEach(
                button => {

                    button.classList.remove(
                        "selected"
                    );

                    if (
                        button.dataset.type ===
                        "PostgreSQL"
                    ) {

                        button.classList.add(
                            "selected"
                        );

                    }

                }
            );


        const portInput =
            document.getElementById(
                "connectionPort"
            );


        if (portInput) {
            portInput.value = "5432";
        }


        if (connectionMessage) {

            connectionMessage.className =
                "connection-message d-none";

            connectionMessage.innerText =
                "";

        }

    }


    /* =========================================================
       VIEW SCHEMA
    ========================================================== */

    const viewSchemaBtn =
        document.getElementById(
            "viewSchemaBtn"
        );


    const quickSchema =
        document.getElementById(
            "quickSchema"
        );


    async function viewSchema() {

        if (!selectedDatabase) {

            alert(
                "Please select a database first."
            );

            return;

        }


        try {

            const response =
                await fetch(
                    `/api/databases/${selectedDatabase.id}/schema`,
                    {
                        method: "GET",
                        headers: getHeaders()
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to load database schema."
                );

            }


            if (
    !Array.isArray(data) ||
    data.length === 0
) {

    alert(
        "No tables were found in this database."
    );

    return;

}


            let message =
                `DATABASE: ${selectedDatabase.name}\n\n`;


            data.forEach(
    table => {

                    message +=
                        `TABLE: ${table.table_name}\n`;

                    table.columns.forEach(
                        column => {

                            message +=
                                `  • ${column.name} (${column.type})\n`;

                        }
                    );

                    message += "\n";

                }
            );


            alert(
                message
            );


        } catch (error) {

            console.error(
                "Schema error:",
                error
            );


            alert(
                `Unable to load schema.\n\n${error.message}`
            );

        }

    }


    if (viewSchemaBtn) {

        viewSchemaBtn.addEventListener(
            "click",
            viewSchema
        );

    }


    if (quickSchema) {

        quickSchema.addEventListener(
            "click",
            viewSchema
        );

    }


    /* =========================================================
       SIDEBAR NAVIGATION
    ========================================================== */

    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(item => {

            item.addEventListener(
                "click",
                event => {

                    event.preventDefault();


                    document
                        .querySelectorAll(
                            ".nav-item"
                        )
                        .forEach(
                            nav =>
                                nav.classList.remove(
                                    "active"
                                )
                        );


                    item.classList.add(
                        "active"
                    );


                    const section =
                        item.dataset.section;


                    if (
                        section ===
                        "databases"
                    ) {

                        document
                            .getElementById(
                                "databaseSection"
                            )
                            ?.scrollIntoView({
                                behavior:
                                    "smooth"
                            });

                    }


                    if (
                        section ===
                        "ask"
                    ) {

                        document
                            .getElementById(
                                "askSection"
                            )
                            ?.scrollIntoView({
                                behavior:
                                    "smooth"
                            });

                    }


                    if (
                        section ===
                        "home"
                    ) {

                        window.scrollTo({
                            top: 0,
                            behavior:
                                "smooth"
                        });

                    }

                }
            );

        });


    /* =========================================================
       GLOBAL SEARCH
    ========================================================== */

    const globalSearch =
        document.getElementById(
            "globalSearch"
        );


    if (globalSearch) {

        globalSearch.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter"
                ) {

                    const value =
                        globalSearch.value.trim();


                    if (!value) {
                        return;
                    }


                    if (questionInput) {

                        questionInput.value =
                            value;

                        questionInput.focus();

                    }


                    document
                        .getElementById(
                            "askSection"
                        )
                        ?.scrollIntoView({
                            behavior:
                                "smooth"
                        });

                }

            }
        );

    }


    /* =========================================================
       KEYBOARD SHORTCUT
    ========================================================== */

    document.addEventListener(
        "keydown",
        event => {

            if (
                (event.ctrlKey ||
                    event.metaKey) &&
                event.key.toLowerCase() ===
                    "k"
            ) {

                event.preventDefault();

                globalSearch?.focus();

            }

        }
    );


});


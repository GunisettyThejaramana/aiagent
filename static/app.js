document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const $ = (id) => document.getElementById(id);

    const questionInput = $("question");
    const askBtn = $("askBtn");
    const answerBox = $("answer");
    const loading = $("loading");

    const sqlSection = $("sqlSection");
    const sqlBox = $("sqlBox");

    const tableSection = $("tableSection");
    const tableHead = $("tableHead");
    const tableBody = $("tableBody");

    const databaseSelect = $("databaseSelect");
    const databaseCount = $("databaseCount");

    const databaseManagementList =
        $("databaseManagementList");

    const chatWindow = $("chatWindow");
    const chatInput = $("chatInput");
    const chatSend = $("chatSend");

    /*
     * VOICE / LANGUAGE ELEMENTS
     *
     * These elements exist in the HTML.
     * Keeping them declared here prevents
     * "voiceStatus is not defined" and similar
     * frontend errors.
     */
    const voiceBtn = $("voiceBtn");
    const inlineVoiceBtn = $("inlineVoiceBtn");
    const languageSelect = $("assistantLanguage");
    const topLanguage = $("topLanguage");
    const speakToggle = $("speakToggle");
    const voiceResponseSetting = $("voiceResponseSetting");

    const documentsList =
        document.getElementById("documentsList");

    const documentsCountText =
        document.getElementById("documentsCountText");

    const refreshDocumentsBtn =
        document.getElementById("refreshDocumentsBtn");

    let databases = [];
    let selectedDatabase = null;
    let selectedDatabaseType = "PostgreSQL";

    let recognition = null;
    let voices = [];

    let sourceModal = null;
    let databaseModal = null;


    function getHeaders() {
        const headers = {
            "Content-Type": "application/json"
        };

        const token =
            localStorage.getItem("token");

        if (token) {
            headers.Authorization =
                `Bearer ${token}`;
        }

        return headers;
    }


    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function normalizeDatabase(db) {
        return {
            id: db.id,

            name:
                db.name ||
                "Unnamed database",

            type:
                db.db_type ||
                db.type ||
                "Database",

            host:
                db.host ||
                "",

            port:
                db.port ||
                "",

            database:
                db.database_name ||
                db.database ||
                "",

            username:
                db.username ||
                ""
        };
    }


    function logoClass(type) {
        const t =
            String(type || "")
                .toLowerCase();

        if (t.includes("mysql")) {
            return "mysql";
        }

        if (
            t.includes("sql server") ||
            t.includes("sqlserver")
        ) {
            return "sqlserver";
        }

        if (t.includes("oracle")) {
            return "oracle";
        }

        return "postgres";
    }


    async function loadDatabases() {

        if (!databaseSelect) {
            return;
        }

        databaseSelect.innerHTML = `
            <option value="">
                Loading databases...
            </option>
        `;

        try {

            const response =
                await fetch(
                    "/api/databases",
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
                    "Unable to load databases."
                );

            }

            databases =
                Array.isArray(data)
                    ? data.map(normalizeDatabase)
                    : [];

            if (databaseCount) {
                databaseCount.textContent =
                    databases.length;
            }

            databaseSelect.innerHTML = "";

            if (!databases.length) {

                databaseSelect.innerHTML = `
                    <option value="">
                        No databases connected
                    </option>
                `;

                selectedDatabase = null;

                renderManagedDatabases();

                return;
            }

            databases.forEach(
                db => {

                    const option =
                        document.createElement(
                            "option"
                        );

                    option.value =
                        db.id;

                    option.textContent =
                        `${db.name} · ${db.type}`;

                    databaseSelect.appendChild(
                        option
                    );

                }
            );

            const previous =
                databases.find(
                    db =>
                        String(db.id) ===
                        String(
                            selectedDatabase?.id
                        )
                );

            selectDatabase(
                previous ||
                databases[0]
            );

            renderManagedDatabases();

        } catch (error) {

            console.error(
                "Database loading error:",
                error
            );

            databaseSelect.innerHTML = `
                <option value="">
                    Unable to load databases
                </option>
            `;

            if (databaseCount) {
                databaseCount.textContent =
                    "0";
            }

            renderManagedDatabases();
        }
    }


    function selectDatabase(db) {

        if (!db) {
            return;
        }

        selectedDatabase =
            db;

        if (databaseSelect) {
            databaseSelect.value =
                String(db.id);
        }

        const label =
            $("selectedSourceLabel");

        if (label) {
            label.textContent =
                `AI is connected to ${db.name} and can query its business data.`;
        }
    }


    if (databaseSelect) {

        databaseSelect.addEventListener(
            "change",
            () => {

                const db =
                    databases.find(
                        item =>
                            String(item.id) ===
                            String(
                                databaseSelect.value
                            )
                    );

                selectDatabase(db);
            }
        );
    }


    function renderManagedDatabases() {

        if (!databaseManagementList) {
            return;
        }

        if (!databases.length) {

            databaseManagementList.innerHTML = `
                <div class="empty-state">

                    <i class="bi bi-database"></i>

                    <strong>
                        No database connections
                    </strong>

                    <span>
                        Add a database to make SQL data
                        available to the AI employee.
                    </span>

                </div>
            `;

            return;
        }

        databaseManagementList.innerHTML =
            databases.map(
                db => `

                <div class="managed-db">

                    <span class="db-logo">
                        <i class="bi bi-database-fill"></i>
                    </span>

                    <div>

                        <strong>
                            ${escapeHtml(db.name)}
                        </strong>

                        <small>
                            ${escapeHtml(
                                db.type
                            )}

                            ·

                            ${escapeHtml(
                                db.host ||
                                "host not shown"
                            )}

                        </small>

                    </div>

                    <span class="status-tag ready">
                        Connected
                    </span>

                    <button
                        class="small-button manage-db-select"
                        data-id="${escapeHtml(db.id)}"
                        type="button"
                    >
                        Use
                    </button>

                </div>
            `
            ).join("");

        document
            .querySelectorAll(
                ".manage-db-select"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        () => {

                            const db =
                                databases.find(
                                    item =>
                                        String(
                                            item.id
                                        ) ===
                                        String(
                                            button.dataset.id
                                        )
                                );

                            selectDatabase(db);

                            showView(
                                "dashboard"
                            );

                            $("askSection")
                                ?.scrollIntoView({
                                    behavior:
                                        "smooth"
                                });
                        }
                    );
                }
            );
    }


    async function askQuestion(
        questionOverride = null
    ) {

        const question =
            (
                questionOverride ??
                questionInput?.value ??
                ""
            ).trim();

        if (!question) {

            showAnswer(
                "Please enter a question."
            );

            return;
        }

        if (!selectedDatabase) {

            showAnswer(
                "Please select a connected database first."
            );

            return;
        }

        resetResults();

        loading?.classList.remove(
            "d-none"
        );

        if (askBtn) {

            askBtn.disabled =
                true;

            askBtn.innerHTML = `
                <span
                    class="spinner-border
                    spinner-border-sm"
                ></span>
            `;
        }

        const requestBody = {

            question:
                question,

            user_id:
                "default_user",

            language:
                topLanguage?.value ||
                languageSelect?.value ||
                "en-US",

            database_id:
                Number(
                    selectedDatabase.id
                )
        };

        try {

            const response =
                await fetch(
                    "/ask",
                    {
                        method: "POST",

                        headers:
                            getHeaders(),

                        body:
                            JSON.stringify(
                                requestBody
                            )
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to get an answer."
                );
            }

            showAnswer(
                data.answer ||
                "No response received from AI."
            );

            displaySQL(
                data.sql ||
                ""
            );

            displayTable(
                data.rows ||
                []
            );

            addChatMessage(
                question,
                "user"
            );

            addChatMessage(
                data.answer ||
                "No answer received.",
                "assistant"
            );

            if (
                !voiceResponseSetting ||
                voiceResponseSetting.checked
            ) {

                speakAnswer(
                    data.answer ||
                    ""
                );
            }

        } catch (error) {

            console.error(
                "Ask error:",
                error
            );

            showAnswer(
                `Unable to get an answer.

${error.message}`
            );

            addChatMessage(
                error.message,
                "assistant"
            );

        } finally {

            loading?.classList.add(
                "d-none"
            );

            if (askBtn) {

                askBtn.disabled =
                    false;

                askBtn.innerHTML = `
                    <i class="bi bi-send-fill"></i>
                `;
            }
        }
    }


    function showAnswer(text) {

        if (!answerBox) {
            return;
        }

        answerBox.textContent =
            text;
    }


    function resetResults() {

        if (answerBox) {

            answerBox.textContent =
                "Analyzing your business data...";
        }

        sqlSection?.classList.add(
            "d-none"
        );

        tableSection?.classList.add(
            "d-none"
        );

        if (sqlBox) {
            sqlBox.textContent =
                "";
        }

        if (tableHead) {
            tableHead.innerHTML =
                "";
        }

        if (tableBody) {
            tableBody.innerHTML =
                "";
        }
    }


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

        if (
            $("showSqlSetting")?.checked !==
            false
        ) {

            sqlSection.classList.remove(
                "d-none"
            );
        }
    }


    function displayTable(rows) {

        if (
            !tableSection ||
            !tableHead ||
            !tableBody
        ) {
            return;
        }

        if (
            !Array.isArray(rows) ||
            !rows.length
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

        tableHead.innerHTML =
            headers
                .map(
                    header =>
                        `<th>${escapeHtml(
                            header
                        )}</th>`
                )
                .join("");

        tableBody.innerHTML =
            rows
                .map(
                    row => `

                    <tr>

                        ${
                            headers
                                .map(
                                    header =>
                                        `<td>${escapeHtml(
                                            row[header] ??
                                            ""
                                        )}</td>`
                                )
                                .join("")
                        }

                    </tr>
                `
                )
                .join("");

        tableSection.classList.remove(
            "d-none"
        );
    }


    function addChatMessage(
        text,
        role
    ) {

        if (!chatWindow) {
            return;
        }

        const emptyState =
            chatWindow.querySelector(
                ".empty-state"
            );

        if (emptyState) {
            emptyState.remove();
        }

        const div =
            document.createElement(
                "div"
            );

        div.className =
            `chat-message ${
                role === "user"
                    ? "user-message"
                    : "assistant-message"
            }`;

        div.innerHTML = `

            ${escapeHtml(text)}

            <time>
                ${
                    new Date().toLocaleTimeString(
                        [],
                        {
                            hour:
                                "2-digit",

                            minute:
                                "2-digit"
                        }
                    )
                }
            </time>

        `;

        chatWindow.appendChild(
            div
        );

        chatWindow.scrollTop =
            chatWindow.scrollHeight;
    }


    /*
     * FEMALE VOICE CONFIGURATION
     */

    const femaleVoiceNames = [

        "zira",
        "heera",
        "kalpana",
        "swara",
        "sara",
        "susan",
        "jenny",
        "aria",
        "libby",
        "sonia",
        "hazel",
        "linda",
        "samantha",
        "eva",
        "natalie",
        "michelle",

        "google uk english female",
        "google us english female",
        "google english female",
        "google hindi female",
        "google tamil female",
        "google indian english female",

        "ava",
        "allison",
        "karen",
        "moira",
        "tessa",

        "female",
        "woman",
        "girl"
    ];


    const maleVoiceNames = [

        "david",
        "mark",
        "george",
        "richard",
        "daniel",
        "james",
        "alex",
        "fred",
        "tom",
        "aaron",
        "arthur",
        "guy",
        "male",
        "man"
    ];


    function scoreFemaleVoice(
        voice,
        language
    ) {

        if (!voice) {
            return -9999;
        }

        const voiceName =
            String(
                voice.name || ""
            ).toLowerCase();

        const voiceLang =
            String(
                voice.lang || ""
            ).toLowerCase();

        const wantedLanguage =
            String(
                language || "en-US"
            ).toLowerCase();

        const wantedBase =
            wantedLanguage
                .split("-")[0];

        const voiceBase =
            voiceLang
                .split("-")[0];

        let score = 0;


        if (
            voiceLang ===
            wantedLanguage
        ) {

            score += 1000;

        } else if (
            voiceBase ===
            wantedBase
        ) {

            score += 700;

        } else {

            score -= 500;
        }


        femaleVoiceNames.forEach(
            femaleName => {

                if (
                    voiceName.includes(
                        femaleName
                    )
                ) {

                    score += 500;
                }
            }
        );


        maleVoiceNames.forEach(
            maleName => {

                if (
                    voiceName === maleName ||
                    voiceName.includes(
                        ` ${maleName} `
                    ) ||
                    voiceName.startsWith(
                        `${maleName} `
                    ) ||
                    voiceName.endsWith(
                        ` ${maleName}`
                    )
                ) {

                    score -= 800;
                }
            }
        );


        if (
            voice.localService
        ) {

            score += 30;
        }

        return score;
    }


    function getBestFemaleVoice(
        language
    ) {

        if (!voices.length) {
            return null;
        }

        const rankedVoices =
            [...voices]
                .map(
                    voice => ({

                        voice,

                        score:
                            scoreFemaleVoice(
                                voice,
                                language
                            )
                    })
                )
                .sort(
                    (a, b) =>
                        b.score -
                        a.score
                );


        console.log(
            "Available speech voices:",

            voices.map(
                voice => ({

                    name:
                        voice.name,

                    language:
                        voice.lang
                })
            )
        );


        console.log(
            "Selected female voice:",

            rankedVoices[0]?.voice?.name,

            rankedVoices[0]?.voice?.lang,

            "score:",

            rankedVoices[0]?.score
        );


        return (
            rankedVoices[0]?.voice ||
            null
        );
    }


    /*
     * TEXT TO SPEECH
     *
     * Fixed:
     * - voiceStatus no longer referenced
     * - languageSelect properly declared
     * - female voice preference preserved
     * - Tamil / Hindi supported
     * - voice setting supported
     */

    function speakAnswer(text) {

        if (
            !text ||
            !window.speechSynthesis
        ) {
            return;
        }


        if (
            voiceResponseSetting &&
            !voiceResponseSetting.checked
        ) {
            return;
        }


        window.speechSynthesis.cancel();

        stopSpeakingVisual();


        const utterance =
            new SpeechSynthesisUtterance(
                text
            );


        const language =
            languageSelect?.value ||
            topLanguage?.value ||
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


        /*
         * Tamil
         */

        if (
            language ===
            "ta-IN"
        ) {

            selectedVoice =
                voices.find(
                    voice => {

                        const voiceLang =
                            String(
                                voice.lang ||
                                ""
                            ).toLowerCase();

                        const voiceName =
                            String(
                                voice.name ||
                                ""
                            ).toLowerCase();


                        return (
                            voiceLang.startsWith(
                                "ta"
                            ) ||

                            voiceName.includes(
                                "tamil"
                            )
                        );
                    }
                );
        }


        /*
         * Hindi
         */

        else if (
            language ===
            "hi-IN"
        ) {

            selectedVoice =
                voices.find(
                    voice => {

                        const voiceLang =
                            String(
                                voice.lang ||
                                ""
                            ).toLowerCase();

                        const voiceName =
                            String(
                                voice.name ||
                                ""
                            ).toLowerCase();


                        return (
                            voiceLang.startsWith(
                                "hi"
                            ) ||

                            voiceName.includes(
                                "hindi"
                            )
                        );
                    }
                );
        }


        /*
         * Other languages:
         * choose best available female voice.
         */

        if (!selectedVoice) {

            selectedVoice =
                getBestFemaleVoice(
                    language
                );
        }


        if (selectedVoice) {

            utterance.voice =
                selectedVoice;
        }


        utterance.onstart =
            () => {

                startSpeakingVisual();

            };


        utterance.onend =
            () => {

                stopSpeakingVisual();

            };


        utterance.onerror =
            error => {

                console.warn(
                    "Speech synthesis error:",
                    error
                );

                stopSpeakingVisual();

            };


        setTimeout(
            () => {

                if (
                    voiceResponseSetting &&
                    !voiceResponseSetting.checked
                ) {
                    return;
                }

                window.speechSynthesis.speak(
                    utterance
                );

            },
            200
        );
    }


        function startSpeakingVisual() {
    try {
        const btn = document.getElementById("voiceBtn");
        if (btn) {
            btn.classList.remove("listening");
            btn.classList.add("speaking");
            btn.innerHTML = '<i class="bi bi-volume-up-fill"></i>';
        }

        const portrait = document.getElementById("assistantPortrait");
        if (portrait) {
            portrait.classList.add("speaking");
        }
    } catch (e) {
        console.warn(e);
    }
}

function stopSpeakingVisual() {
    try {
        const btn = document.getElementById("voiceBtn");
        if (btn) {
            btn.classList.remove("speaking");
            btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        }

        const portrait = document.getElementById("assistantPortrait");
        if (portrait) {
            portrait.classList.remove("speaking");
        }
    } catch (e) {
        console.warn(e);
    }
}

    function loadVoices() {

        if (
            !window.speechSynthesis
        ) {
            return;
        }

        voices =
            window.speechSynthesis
                .getVoices();


        console.log(
            "Speech voices loaded:",
            voices.length
        );


        if (voices.length) {

            console.table(
                voices.map(
                    voice => ({

                        Name:
                            voice.name,

                        Language:
                            voice.lang,

                        Local:
                            voice.localService
                    })
                )
            );
        }
    }


    loadVoices();


    if (
        window.speechSynthesis
    ) {

        window.speechSynthesis.onvoiceschanged =
            () => {

                loadVoices();

            };
    }


    /*
     * SPEECH RECOGNITION
     */

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (SpeechRecognition) {

        recognition =
            new SpeechRecognition();


        recognition.continuous =
            false;


        recognition.interimResults =
            false;


        recognition.onstart =
            () => {

                voiceBtn
                    ?.classList
                    .add(
                        "listening"
                    );


                inlineVoiceBtn
                    ?.classList
                    .add(
                        "listening"
                    );
            };


        recognition.onresult =
            event => {

                const transcript =
                    event
                        .results[0][0]
                        .transcript;


                if (questionInput) {

                    questionInput.value =
                        transcript;
                }


                if (chatInput) {

                    chatInput.value =
                        transcript;
                }


                askQuestion(
                    transcript
                );
            };


        recognition.onend =
            () => {

                voiceBtn
                    ?.classList
                    .remove(
                        "listening"
                    );


                inlineVoiceBtn
                    ?.classList
                    .remove(
                        "listening"
                    );
            };


        recognition.onerror =
            error => {

                console.warn(
                    "Speech recognition:",
                    error
                );
            };
    }


    function startVoice() {

        if (!recognition) {

            showAnswer(
                "Voice input is not supported by this browser."
            );

            return;
        }


        recognition.lang =
            languageSelect?.value ||
            topLanguage?.value ||
            "en-US";


        try {

            recognition.start();

        } catch (_) {

            /*
             * Recognition may already
             * be running.
             */
        }
    }


    voiceBtn
        ?.addEventListener(
            "click",
            startVoice
        );


    inlineVoiceBtn
        ?.addEventListener(
            "click",
            startVoice
        );


    /*
     * NAVIGATION
     */

    function showView(name) {

        document
            .querySelectorAll(
                ".view"
            )
            .forEach(
                view =>
                    view.classList.add(
                        "hidden-view"
                    )
            );


        const target =
            $(`${name}View`);


        if (target) {

            target.classList.remove(
                "hidden-view"
            );
        }


        document
            .querySelectorAll(
                ".nav-item"
            )
            .forEach(
                item => {

                    item.classList.toggle(
                        "active",
                        item.dataset.view ===
                        name
                    );
                }
            );


        if (
            name ===
            "databases"
        ) {

            renderManagedDatabases();
        }
    }


    document
        .querySelectorAll(
            ".nav-item"
        )
        .forEach(
            item => {

                item.addEventListener(
                    "click",
                    () => {

                        showView(
                            item.dataset.view
                        );
                    }
                );
            }
        );


    document
        .querySelectorAll(
            "[data-view-target]"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const view =
                            button.dataset
                                .viewTarget;

                        showView(
                            view
                        );
                    }
                );
            }
        );


    /*
     * ASK BUTTON
     */

    if (askBtn) {

        askBtn.addEventListener(
            "click",
            () => {

                askQuestion();

            }
        );
    }


    /*
     * ENTER KEY
     */

    if (questionInput) {

        questionInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key ===
                    "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    askQuestion();
                }
            }
        );
    }


    /*
     * SAMPLE QUESTIONS
     */

    document
        .querySelectorAll(
            ".sample-question"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        if (
                            !questionInput
                        ) {
                            return;
                        }


                        questionInput.value =
                            button
                                .textContent
                                .trim();


                        questionInput.focus();
                    }
                );
            }
        );


    /*
     * RIGHT CHAT SEND
     */

    if (chatSend) {

        chatSend.addEventListener(
            "click",
            () => {

                const value =
                    chatInput
                        ?.value
                        .trim();


                if (!value) {
                    return;
                }


                if (questionInput) {

                    questionInput.value =
                        value;
                }


                if (chatInput) {

                    chatInput.value =
                        "";
                }


                showView(
                    "dashboard"
                );


                askQuestion(
                    value
                );
            }
        );
    }


    /*
     * CHAT ENTER
     */

    if (chatInput) {

        chatInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key ===
                    "Enter"
                ) {

                    event.preventDefault();

                    chatSend?.click();
                }
            }
        );
    }


    /*
     * CHAT TABS
     */

    document
        .querySelectorAll(
            ".chat-tab"
        )
        .forEach(
            tab => {

                tab.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".chat-tab"
                            )
                            .forEach(
                                item =>
                                    item.classList
                                        .remove(
                                            "active"
                                        )
                            );


                        tab.classList.add(
                            "active"
                        );


                        if (
                            tab.dataset.tab ===
                            "history"
                        ) {

                            chatWindow.innerHTML = `

                                <div
                                    class="empty-state"
                                    style="min-height:160px"
                                >

                                    <i class="bi bi-clock-history"></i>

                                    <strong>
                                        Conversation history
                                    </strong>

                                    <span>
                                        Previous questions
                                        will appear here.
                                    </span>

                                </div>
                            `;

                        } else {

                            chatWindow.innerHTML = `

                                <div
                                    class="empty-state"
                                    style="min-height:160px"
                                >

                                    <i class="bi bi-chat-dots"></i>

                                    <strong>
                                        No conversation yet
                                    </strong>

                                    <span>
                                        Ask a question to start
                                        the conversation.
                                    </span>

                                </div>
                            `;
                        }
                    }
                );
            }
        );


    /*
     * DATABASE MODAL
     */

    const databaseModalElement =
        $("databaseModal");


    if (
        databaseModalElement &&
        window.bootstrap
    ) {

        databaseModal =
            new bootstrap.Modal(
                databaseModalElement
            );
    }


    function openDatabaseModal() {

        databaseModal?.show();

    }


    $("manageDatabaseButton")
        ?.addEventListener(
            "click",
            openDatabaseModal
        );


    /*
     * DATABASE TYPE
     */

    document
        .querySelectorAll(
            ".database-type"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".database-type"
                            )
                            .forEach(
                                item =>
                                    item.classList
                                        .remove(
                                            "selected"
                                        )
                            );


                        button.classList.add(
                            "selected"
                        );


                        selectedDatabaseType =
                            button.dataset.type;


                        const ports = {

                            PostgreSQL:
                                "5432",

                            MySQL:
                                "3306",

                            "SQL Server":
                                "1433",

                            Oracle:
                                "1521"
                        };


                        const portInput =
                            $("connectionPort");


                        if (portInput) {

                            portInput.value =
                                ports[
                                    selectedDatabaseType
                                ] ||
                                "";
                        }
                    }
                );
            }
        );


    /*
     * TEST DATABASE CONNECTION
     */

    $("testConnectionBtn")
        ?.addEventListener(
            "click",
            async () => {

                const payload = {

                    db_type:
                        selectedDatabaseType
                            .toLowerCase()
                            .replace(
                                /\s+/g,
                                ""
                            ),

                    host:
                        $("connectionHost")
                            ?.value
                            .trim(),

                    port:
                        Number(
                            $("connectionPort")
                                ?.value
                        ),

                    database_name:
                        $("connectionDatabase")
                            ?.value
                            .trim(),

                    username:
                        $("connectionUsername")
                            ?.value
                            .trim(),

                    password:
                        $("connectionPassword")
                            ?.value
                };


                if (
                    !payload.host ||
                    !payload.port ||
                    !payload.database_name ||
                    !payload.username ||
                    !payload.password
                ) {

                    showConnectionMessage(
                        "Please fill all connection details.",
                        "error"
                    );

                    return;
                }


                const button =
                    $("testConnectionBtn");


                button.disabled =
                    true;


                button.textContent =
                    "Testing...";


                try {

                    const response =
                        await fetch(
                            "/api/databases/test",
                            {
                                method:
                                    "POST",

                                headers:
                                    getHeaders(),

                                body:
                                    JSON.stringify(
                                        payload
                                    )
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


                    showConnectionMessage(

                        data.message ||

                        (
                            data.success
                                ? "Connection successful."
                                : "Connection failed."
                        ),

                        data.success
                            ? "success"
                            : "error"
                    );


                } catch (error) {

                    showConnectionMessage(
                        error.message,
                        "error"
                    );


                } finally {

                    button.disabled =
                        false;


                    button.innerHTML = `

                        <i class="bi bi-plug"></i>

                        Test Connection

                    `;
                }
            }
        );


    /*
     * SAVE DATABASE
     */

    $("saveDatabaseBtn")
        ?.addEventListener(
            "click",
            async () => {

                const payload = {

                    name:
                        $("connectionName")
                            ?.value
                            .trim(),

                    db_type:
                        selectedDatabaseType
                            .toLowerCase()
                            .replace(
                                /\s+/g,
                                ""
                            ),

                    host:
                        $("connectionHost")
                            ?.value
                            .trim(),

                    port:
                        Number(
                            $("connectionPort")
                                ?.value
                        ),

                    database_name:
                        $("connectionDatabase")
                            ?.value
                            .trim(),

                    username:
                        $("connectionUsername")
                            ?.value
                            .trim(),

                    password:
                        $("connectionPassword")
                            ?.value
                };


                if (
                    !payload.name ||
                    !payload.host ||
                    !payload.port ||
                    !payload.database_name ||
                    !payload.username ||
                    !payload.password
                ) {

                    showConnectionMessage(
                        "Please complete all database fields.",
                        "error"
                    );

                    return;
                }


                const button =
                    $("saveDatabaseBtn");


                button.disabled =
                    true;


                button.textContent =
                    "Saving...";


                try {

                    const response =
                        await fetch(
                            "/api/databases",
                            {
                                method:
                                    "POST",

                                headers:
                                    getHeaders(),

                                body:
                                    JSON.stringify(
                                        payload
                                    )
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


                    await loadDatabases();


                    setTimeout(
                        () => {

                            databaseModal?.hide();

                        },
                        500
                    );


                } catch (error) {

                    showConnectionMessage(
                        error.message,
                        "error"
                    );


                } finally {

                    button.disabled =
                        false;


                    button.innerHTML = `

                        <i class="bi bi-check2"></i>

                        Save Database

                    `;
                }
            }
        );


    function showConnectionMessage(
        message,
        type
    ) {

        const box =
            $("connectionMessage");


        if (!box) {
            return;
        }


        box.textContent =
            message;


        box.className =
            `connection-message ${type}`;
    }


    /*
     * SOURCE MODAL
     */

    const sourceModalElement =
        $("sourceModal");


    if (
        sourceModalElement &&
        window.bootstrap
    ) {

        sourceModal =
            new bootstrap.Modal(
                sourceModalElement
            );
    }


    function openSourceModal() {

        sourceModal?.show();

    }


    $("addSourceButton")
        ?.addEventListener(
            "click",
            openSourceModal
        );


    $("documentSourceButton")
        ?.addEventListener(
            "click",
            openSourceModal
        );


    /*
     * SOURCE TYPE
     */

    document
        .querySelectorAll(
            ".source-type"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".source-type"
                            )
                            .forEach(
                                item =>
                                    item.classList
                                        .remove(
                                            "selected"
                                        )
                            );


                        button.classList.add(
                            "selected"
                        );
                    }
                );
            }
        );


    /*
     * SAVE SOURCE
     */

    $("saveSourceButton")
        ?.addEventListener(
            "click",
            () => {

                const name =
                    $("sourceName")
                        ?.value
                        .trim();


                const path =
                    $("sourcePath")
                        ?.value
                        .trim();


                const box =
                    $("sourceMessage");


                if (
                    !name ||
                    !path
                ) {

                    box.textContent =
                        "Enter a source name and location.";


                    box.className =
                        "source-message error";


                    return;
                }


                box.textContent =
                    `Source "${name}" configured for ${path}. Backend indexing is required to make its files searchable.`;


                box.className =
                    "source-message success";


                setTimeout(
                    () => {

                        sourceModal?.hide();

                    },
                    900
                );
            }
        );


    /*
     * VIEW DATABASE SCHEMA
     */

    $("viewSchemaBtn")
        ?.addEventListener(
            "click",
            async () => {

                if (!selectedDatabase) {

                    showAnswer(
                        "Please connect and select a database first."
                    );

                    return;
                }


                try {

                    const response =
                        await fetch(
                            `/api/databases/${selectedDatabase.id}/schema`,
                            {
                                headers:
                                    getHeaders()
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Unable to load schema."
                        );
                    }


                    if (
                        !Array.isArray(data) ||
                        !data.length
                    ) {

                        showAnswer(
                            "No tables were found in this database."
                        );

                        return;
                    }


                    const text =
                        data
                            .map(
                                table => {

                                    const columns =
                                        (
                                            table.columns ||
                                            []
                                        )
                                            .map(
                                                column =>
                                                    `• ${column.name} (${column.type})`
                                            )
                                            .join(
                                                "\n"
                                            );


                                    return `

TABLE: ${table.table_name}

${columns}

                                    `.trim();
                                }
                            )
                            .join(
                                "\n\n"
                            );


                    showAnswer(
                        `DATABASE: ${selectedDatabase.name}\n\n${text}`
                    );


                } catch (error) {

                    showAnswer(
                        `Unable to load schema.

${error.message}`
                    );
                }
            }
        );


    /*
     * LANGUAGE SYNCHRONIZATION
     */

    [
        "topLanguage",
        "assistantLanguage"
    ]
        .forEach(
            id => {

                $(id)
                    ?.addEventListener(
                        "change",
                        () => {

                            const value =
                                $(id).value;


                            if (
                                topLanguage
                            ) {

                                topLanguage.value =
                                    value;
                            }


                            if (
                                languageSelect
                            ) {

                                languageSelect.value =
                                    value;
                            }


                            loadVoices();
                        }
                    );
            }
        );


    /*
     * ATTACH BUTTON
     */

    $("attachButton")
        ?.addEventListener(
            "click",
            () => {

                showView(
                    "documents"
                );


                $("documentSearch")
                    ?.focus();
            }
        );


    /*
     * DOCUMENT SEARCH
     */

    $("documentSearch")
        ?.addEventListener(
            "input",
            event => {

                const query =
                    event.target.value
                        .toLowerCase();


                document
                    .querySelectorAll(
                        "#documentLibrary .library-card"
                    )
                    .forEach(
                        card => {

                            card.style.display =
                                card.textContent
                                    .toLowerCase()
                                    .includes(
                                        query
                                    )
                                        ? ""
                                        : "none";
                        }
                    );
            }
        );


    /*
     * SETTINGS LANGUAGE
     */

    $("settingsLanguage")
        ?.addEventListener(
            "change",
            event => {

                const value =
                    event.target.value;


                const map = {

                    English:
                        "en-US",

                    Hindi:
                        "hi-IN",

                    Tamil:
                        "ta-IN"
                };


                const language =
                    map[value] ||
                    "en-US";


                if (
                    topLanguage
                ) {

                    topLanguage.value =
                        language;
                }


                if (
                    languageSelect
                ) {

                    languageSelect.value =
                        language;
                }


                loadVoices();
            }
        );


    /*
     * VOICE RESPONSE SETTING
     *
     * This connects the Settings checkbox
     * with the volume button on the AI employee.
     */

    if (voiceResponseSetting) {

        voiceResponseSetting.addEventListener(
            "change",
            () => {

                if (
                    voiceResponseSetting.checked
                ) {

                    if (speakToggle) {

                        speakToggle.innerHTML =
                            '<i class="bi bi-volume-up"></i>';

                        speakToggle.classList.remove(
                            "muted"
                        );
                    }

                } else {

                    if (
                        window.speechSynthesis
                    ) {

                        window.speechSynthesis.cancel();
                    }


                    stopSpeakingVisual();


                    if (speakToggle) {

                        speakToggle.innerHTML =
                            '<i class="bi bi-volume-mute"></i>';

                        speakToggle.classList.add(
                            "muted"
                        );
                    }
                }
            }
        );
    }


    /*
     * TOP VOLUME BUTTON
     */

    if (speakToggle) {

        speakToggle.addEventListener(
            "click",
            () => {

                if (!voiceResponseSetting) {
                    return;
                }


                voiceResponseSetting.checked =
                    !voiceResponseSetting.checked;


                voiceResponseSetting.dispatchEvent(
                    new Event(
                        "change"
                    )
                );
            }
        );
    }


    /*
     * KEYBOARD SHORTCUT
     */

    document.addEventListener(
        "keydown",
        event => {

            if (
                (
                    event.ctrlKey ||
                    event.metaKey
                ) &&

                event.key.toLowerCase() ===
                "k"
            ) {

                event.preventDefault();

                questionInput?.focus();
            }
        }
    );


    /*
     * INITIAL LOAD
     */

    loadDatabases();


    /*
     * Chrome / Edge sometimes populate
     * speech voices asynchronously.
     */

    setTimeout(
        () => {

            loadVoices();

        },
        500
    );


    setTimeout(
        () => {

            loadVoices();

        },
        1500
    );

});
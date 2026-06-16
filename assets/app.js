(function () {
    let recognition = null;
    let isRecording = false;

    const THEME_MAP = {
        "Nikola Tesla": "tesla",
        "Leonardo da Vinci": "davinci",
        "Marie Curie": "curie",
        "Alan Turing": "turing",
        "Ada Lovelace": "lovelace",
        "Cleopatra": "cleopatra",
        "Alejandro Magno": "alexander",
        "Julio César": "caesar",
        "Gengis Kan": "genghis",
        "Charles Babbage": "babbage",
        "Grace Hopper": "hopper",
    };

    function setReactValue(element, value) {
        if (!element) return;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
        const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
        if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
            prototypeValueSetter.call(element, value);
        } else if (valueSetter) {
            valueSetter.call(element, value);
        } else {
            element.value = value;
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
    }

    window.selectCharacter = function (name) {
        document.querySelectorAll('.character-card').forEach(card => {
            card.classList.toggle('active', card.getAttribute('data-name') === name);
        });

        const themeId = THEME_MAP[name] || "tesla";
        document.body.className = `theme-${themeId}`;

        const input = document.querySelector('#hidden-character textarea, #hidden-character input, #hidden-character select');
        if (input) setReactValue(input, name);
    };

    function initSpeechRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return null;
        const rec = new SR();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = 'es-ES';
        rec.onstart = () => { isRecording = true; updateMicUI(true); };
        rec.onend = () => { isRecording = false; updateMicUI(false); };
        rec.onerror = (e) => {
            isRecording = false;
            updateMicUI(false);
            if (e.error !== 'no-speech' && e.error !== 'aborted') {
                console.warn('Speech recognition error:', e.error);
            }
        };
        rec.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            const ta = document.querySelector('textarea');
            if (ta) setReactValue(ta, transcript);
        };
        return rec;
    }

    function toggleSpeechRecognition() {
        if (!recognition) recognition = initSpeechRecognition();
        if (!recognition) { alert("Tu navegador no soporta voz. Usa Chrome o Edge."); return; }
        isRecording ? recognition.stop() : recognition.start();
    }

    function updateMicUI(recording) {
        document.querySelectorAll('.voice-input-btn').forEach(btn => {
            btn.classList.toggle('recording', recording);
            btn.textContent = recording ? '🎤🔴' : '🎤';
            btn.title = recording ? "Escuchando..." : "Dictar pregunta con voz";
        });
    }

    function injectMicButton() {
        document.querySelectorAll('div[data-testid="textbox"]').forEach(c => {
            if (c.querySelector('.voice-input-btn')) return;
            c.style.position = 'relative';
            const btn = document.createElement('button');
            btn.className = 'voice-input-btn';
            btn.textContent = '🎤';
            btn.type = 'button';
            btn.title = "Dictar pregunta con voz";
            btn.onclick = (e) => { e.preventDefault(); toggleSpeechRecognition(); };
            c.appendChild(btn);
        });
    }

    function syncActiveCharacterState() {
        const input = document.querySelector('#hidden-character textarea, #hidden-character input');
        if (!input || !input.value) return;
        const name = input.value;
        document.querySelectorAll('.character-card').forEach(card => {
            card.classList.toggle('active', card.getAttribute('data-name') === name);
        });
        const themeId = THEME_MAP[name] || "tesla";
        if (!document.body.classList.contains(`theme-${themeId}`)) {
            document.body.className = `theme-${themeId}`;
        }
    }

    let injectScheduled = false;
    function scheduleInject() {
        if (injectScheduled) return;
        injectScheduled = true;
        requestAnimationFrame(() => {
            injectMicButton();
            injectScheduled = false;
        });
    }

    function startDynamicChecking() {
        injectMicButton();
        syncActiveCharacterState();

        // Inject mic button reactively on DOM changes instead of polling
        const observer = new MutationObserver(scheduleInject);
        observer.observe(document.body, { childList: true, subtree: true });

        // Character state sync at a low frequency (fallback for edge cases)
        setInterval(syncActiveCharacterState, 2000);
    }

    document.readyState === 'loading'
        ? document.addEventListener('DOMContentLoaded', startDynamicChecking)
        : startDynamicChecking();
})();

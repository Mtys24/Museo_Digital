(function () {
    // Variable para rastrear la grabación de voz
    let recognition = null;
    let isRecording = false;

    // Función universal para actualizar el valor de un input/textarea en React
    function setReactValue(element, value) {
        if (!element) return;
        
        console.log("Estableciendo valor React a:", value, element);
        const lastValue = element.value;
        
        // Obtener el setter nativo de la clase prototype correspondiente
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
        
        // Disparar los eventos necesarios para que React se entere de los cambios
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Función para cambiar de personaje desde HTML personalizado
    window.selectCharacter = function (name) {
        console.log("window.selectCharacter llamada con:", name);
        
        // Encontrar todas las tarjetas y actualizar la clase activa en el DOM
        const cards = document.querySelectorAll('.character-card');
        cards.forEach(card => {
            if (card.getAttribute('data-name') === name) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });

        // Cambiar la clase de tema en el body para las transiciones CSS
        const themeId = name === "Nikola Tesla" ? "tesla" : (name === "Leonardo da Vinci" ? "davinci" : "curie");
        document.body.className = '';
        document.body.classList.add(`theme-${themeId}`);
        console.log("Tema actualizado en body:", `theme-${themeId}`);

        // Encontrar el selector oculto de Gradio (input/textarea) y actualizarlo
        const input = document.querySelector('#hidden-character textarea, #hidden-character input, #hidden-character select');
        if (input) {
            setReactValue(input, name);
            console.log("Selector de Gradio actualizado exitosamente.");
        } else {
            console.warn("No se encontró el control de texto/select oculto bajo #hidden-character.");
            // Diagnóstico de elementos bajo #hidden-character
            const container = document.querySelector('#hidden-character');
            if (container) {
                console.log("HTML del contenedor #hidden-character:", container.innerHTML);
            } else {
                console.log("No se encontró el contenedor #hidden-character.");
            }
        }
    };

    // Inicializar reconocimiento de voz (Web Speech API)
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("Este navegador no soporta reconocimiento de voz nativo.");
            return null;
        }

        const rec = new SpeechRecognition();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = 'es-ES';

        rec.onstart = function () {
            isRecording = true;
            updateMicUI(true);
        };

        rec.onend = function () {
            isRecording = false;
            updateMicUI(false);
        };

        rec.onerror = function (event) {
            console.error("Error en reconocimiento de voz:", event.error);
            isRecording = false;
            updateMicUI(false);
        };

        rec.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            console.log("Texto dictado:", transcript);
            
            // Buscar el textbox de Gradio e inyectar el texto
            const textareas = document.querySelectorAll('.input-row-container textarea, #msg-box textarea, textarea[data-testid="textbox"]');
            if (textareas.length > 0) {
                setReactValue(textareas[0], transcript);
            }
        };

        return rec;
    }

    function toggleSpeechRecognition() {
        if (!recognition) {
            recognition = initSpeechRecognition();
        }
        
        if (!recognition) {
            alert("Tu navegador no soporta entrada de voz. Te recomendamos usar Google Chrome o Microsoft Edge.");
            return;
        }

        if (isRecording) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }

    // Actualizar la interfaz del micrófono
    function updateMicUI(recording) {
        const micBtns = document.querySelectorAll('.voice-input-btn');
        micBtns.forEach(btn => {
            if (recording) {
                btn.classList.add('recording');
                btn.innerHTML = '🎤🔴';
                btn.title = "Escuchando... Haz clic para detener";
            } else {
                btn.classList.remove('recording');
                btn.innerHTML = '🎤';
                btn.title = "Dictar pregunta con voz";
            }
        });
    }

    // Inyectar el botón de micrófono en la barra de texto
    function injectMicButton() {
        const containers = document.querySelectorAll('.input-row-container, div[data-testid="textbox"]');
        containers.forEach(container => {
            if (container.querySelector('.voice-input-btn')) return;

            container.style.position = 'relative';

            const micBtn = document.createElement('button');
            micBtn.className = 'voice-input-btn';
            micBtn.innerHTML = '🎤';
            micBtn.type = 'button';
            micBtn.title = "Dictar pregunta con voz";
            
            micBtn.onclick = function (e) {
                e.preventDefault();
                e.stopPropagation();
                toggleSpeechRecognition();
            };

            container.appendChild(micBtn);
            console.log("Botón de micrófono inyectado con éxito.");
        });
    }

    // Sincronizar el estado del frontend con el personaje activo actual
    function syncActiveCharacterState() {
        const gradioSelectorInput = document.querySelector('#hidden-character textarea, #hidden-character input, #hidden-character select');
        if (gradioSelectorInput && gradioSelectorInput.value) {
            const currentCharacterName = gradioSelectorInput.value;
            
            const cards = document.querySelectorAll('.character-card');
            let found = false;
            cards.forEach(card => {
                if (card.getAttribute('data-name') === currentCharacterName) {
                    card.classList.add('active');
                    found = true;
                } else {
                    card.classList.remove('active');
                }
            });

            if (found) {
                const themeId = currentCharacterName === "Nikola Tesla" ? "tesla" : (currentCharacterName === "Leonardo da Vinci" ? "davinci" : "curie");
                if (!document.body.classList.contains(`theme-${themeId}`)) {
                    document.body.className = '';
                    document.body.classList.add(`theme-${themeId}`);
                    console.log("Sincronización: tema del body cambiado a", themeId);
                }
            }
        }
    }

    // Loop de chequeo y sincronización periódica (robusto ante re-renders de Gradio)
    function startDynamicChecking() {
        setInterval(() => {
            injectMicButton();
            syncActiveCharacterState();
        }, 1000);
    }

    // Inicialización del script
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            startDynamicChecking();
        });
    } else {
        startDynamicChecking();
    }
})();

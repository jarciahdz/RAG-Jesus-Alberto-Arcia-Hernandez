document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function sendMessage() {
    const inputElement = document.getElementById('chat-input');
    const message = inputElement.value;

    if (message.trim() === '') {
        return;
    }

    displayMessage('Tu', message, 'user');
    inputElement.value = '';

    const typingIndicator = displayTypingIndicator();

    const variable = '34.227.79.203';

    // CSRF_mejorar_pregunta
    fetch(`http://${variable}:5001`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        // console.log("CSRF Token (mejorar_pregunta):", data.csrf_token);
        const csrfTokenImprove = data.csrf_token;

        // mejorar_pregunta
        return fetch(`http://${variable}:5001/improve_question`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Access-Key': 'f37c222d2efe960846d2e6771e50ae090c8a6c3c01c7e38c',
                'Origin': `http://${variable}:5001`,
                'X-CSRFToken': csrfTokenImprove
            },
            body: JSON.stringify({ question: message })
        });
    })
    .then(response => response.json())
    .then(data => {
        const improvedQuestion = data.question;
        // console.log("Improved Question:", improvedQuestion);

        // CSRF_obtener_embedding
        return fetch(`http://${variable}:5002`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            // console.log("CSRF Token (obtener_embedding):", data.csrf_token);
            const csrfTokenEmbedding = data.csrf_token;

            // obtener_embedding
            return fetch(`http://${variable}:5002/get_embedding`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Key': 'f37c222d2efe960846d2e6771e50ae090c8a6c3c01c7e38c',
                    'Origin': `http://${variable}:5002`,
                    'X-CSRFToken': csrfTokenEmbedding
                },
                body: JSON.stringify({ question: improvedQuestion })
            });
        });
    })
    .then(response => response.json())
    .then(data => {
        const embedding = data.embedding;
        const question = data.question;
        // console.log("Embedding:", embedding);

        // CSRF_normalizar_embeddings
        return fetch(`http://${variable}:5003`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            // console.log("CSRF Token (normalizar_embeddings):", data.csrf_token);
            const csrfTokenNormalize = data.csrf_token;

            // normalizar_embeddings
            return fetch(`http://${variable}:5003/normalize_embedding`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Key': 'f37c222d2efe960846d2e6771e50ae090c8a6c3c01c7e38c',
                    'Origin': `http://${variable}:5003`,
                    'X-CSRFToken': csrfTokenNormalize
                },
                body: JSON.stringify({ question: question, embedding: embedding })
            });
        });
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text) });
        }
        return response.json();
    })
    .then(data => {
        const normalizedEmbedding = data.embedding;
        const normalizedQuestion = data.question;
        // console.log("Normalized Embedding:", normalizedEmbedding);

        // CSRF_recuperar_embeddings
        return fetch(`http://${variable}:5004`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            // console.log("CSRF Token (recuperar_embeddings):", data.csrf_token);
            const csrfTokenRetrieve = data.csrf_token;

            // recuperar_embeddings
            return fetch(`http://${variable}:5004/get_relevant_embeddings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Key': 'f37c222d2efe960846d2e6771e50ae090c8a6c3c01c7e38c',
                    'Origin': `http://${variable}:5004`,
                    'X-CSRFToken': csrfTokenRetrieve
                },
                body: JSON.stringify({ question: normalizedQuestion, embedding: normalizedEmbedding })
            });
        });
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text) });
        }
        return response.json();
    })
    .then(data => {
        const relevantMovies = data.relevant_movies;
        const relevantQuestion = data.question;
        // console.log("Relevant Movies:", relevantMovies);

        // CSRF_generar_respuesta
        return fetch(`http://${variable}:5005`, {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            // console.log("CSRF Token (generar_respuesta):", data.csrf_token);
            const csrfTokenGenerate = data.csrf_token;

            // generar_respuesta
            return fetch(`http://${variable}:5005/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Key': 'f37c222d2efe960846d2e6771e50ae090c8a6c3c01c7e38c',
                    'Origin': `http://${variable}:5005`,
                    'X-CSRFToken': csrfTokenGenerate
                },
                body: JSON.stringify({ question: relevantQuestion, relevant_movies: relevantMovies })
            });
        });
    })
    .then(response => response.json())
    .then(data => {
        const answer = data.answer;
        // console.log("Answer:", answer);
        removeTypingIndicator(typingIndicator);
        displayMessage('Asistente inteligente', answer, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        removeTypingIndicator(typingIndicator);
        displayMessage('Asistente inteligente', `An error occurred: ${error.message}`, 'bot');
    });
}

function displayMessage(sender, message, className) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('p');
    messageElement.classList.add(className);

    if (typeof message !== 'string') {
        message = JSON.stringify(message);
    }

    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = message.split(urlRegex);

    parts.forEach(part => {
        if (urlRegex.test(part)) {
            const link = document.createElement('a');
            link.href = part;
            link.textContent = part;
            link.target = "_blank";
            messageElement.appendChild(link);
        } else {
            const text = document.createTextNode(part);
            messageElement.appendChild(text);
        }
    });

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function displayTypingIndicator() {
    const chatBox = document.getElementById('chat-box');
    const typingElement = document.createElement('p');
    typingElement.classList.add('typing', 'bot');
    typingElement.textContent = 'Asistente inteligente está escribiendo';

    const dot1 = document.createElement('span');
    dot1.classList.add('typing-indicator');
    typingElement.appendChild(dot1);

    const dot2 = document.createElement('span');
    dot2.classList.add('typing-indicator');
    typingElement.appendChild(dot2);

    const dot3 = document.createElement('span');
    dot3.classList.add('typing-indicator');
    typingElement.appendChild(dot3);

    chatBox.appendChild(typingElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    return typingElement;
}

function removeTypingIndicator(typingElement) {
    typingElement.remove();
}

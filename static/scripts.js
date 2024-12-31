

const maxWords = 400;

async function performNER(inputId) {
    const text = document.getElementById(inputId).innerText || document.getElementById(inputId).value;

    const response = await fetch('/ner', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    });
    const result = await response.json();
    displayNERResults(result);
}

async function performTopicModeling(inputId) {
    const text = document.getElementById(inputId).innerText || document.getElementById(inputId).value;

    const response = await fetch('/topic_modeling', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    });
    const result = await response.json();
    displayTopicModelingResults(result);
}

function displayNERResults(result) {
    const nerResultsContainer = document.getElementById('ner-results-container');
    const nerResults = document.getElementById('ner-results');
    const nerHeader = document.getElementById('ner-header');

    nerResults.innerHTML = '';
    result.entities.forEach(([entity, label]) => {
        const p = document.createElement('p');
        p.textContent = `${entity} - ${label}`;
        nerResults.appendChild(p);
    });

    nerResultsContainer.classList.remove('hidden');
    nerHeader.style.display = 'block';
}

function interpretTopicModelingResults(topics) {
    return topics.map(topic => {
        const terms = topic.split('+');
        const mainTerms = terms.slice(0, 3).map(term => term.split('*')[1].replace(/"/g, ''));
        return `This topic is mainly about: ${mainTerms.join(', ')}.`;
    });
}

function displayTopicModelingResults(result) {
    const topicModelingResultsContainer = document.getElementById('topic-modeling-results-container');
    const topicModelingResults = document.getElementById('topic-modeling-results');
    const topicHeader = document.getElementById('topic-header');

    topicModelingResults.innerHTML = '';
    const interpretations = interpretTopicModelingResults(result.topics);
    result.topics.forEach((topic, index) => {
        const p = document.createElement('p');
        p.textContent = topic;

        const interpretation = document.createElement('p');
        interpretation.textContent = interpretations[index];
        interpretation.className = 'interpretation';

        topicModelingResults.appendChild(p);
        topicModelingResults.appendChild(interpretation);
    });

    topicModelingResultsContainer.classList.remove('hidden');
    topicHeader.style.display = 'block';
}

function copyToClipboard() {
    const summaryText = document.getElementById('summary-text').innerText;
    const textArea = document.createElement('textarea');
    textArea.value = summaryText;
    document.body.appendChild(textArea);
    textArea.select();
    try {
        document.execCommand('copy');
        // Create a message element
        const message = document.createElement('div');
        message.textContent = 'Copied';
        message.style.position = 'fixed';
        message.style.bottom = '20px';
        message.style.right = '20px';
        message.style.backgroundColor = 'black';
        message.style.padding = '10px';
        message.style.borderRadius = '5px';
        message.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
        document.body.appendChild(message);
        // Remove the message after 2 seconds
        setTimeout(() => {
            document.body.removeChild(message);
        }, 2000);
    } catch (err) {
        console.error('Failed to copy text: ', err);
    }
    document.body.removeChild(textArea);
}


async function predictEmotion() {
    const text = document.getElementById('text-input').value;
    const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;

    if (wordCount > maxWords) {
        displayAlert(`Input exceeds the maximum allowed words (${maxWords}). Please shorten your text.`);
        return;
    } else {
        hideAlert();
    }

    const response = await fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    });
    const result = await response.json();
    displayResults(result);
    storeTextHistory(text);
}

function displayResults(result) {
    const emotionsDiv = document.getElementById('emotions');
    const sentimentDiv = document.getElementById('sentiment');

    // Clear previous results
    emotionsDiv.innerHTML = '';
    sentimentDiv.innerHTML = '';

    // Display emotion analysis results with visualization
    for (const [emotion, score] of Object.entries(result.emotions)) {
        const container = document.createElement('div');
        container.className = 'emotion-container';

        const label = document.createElement('label');
        label.textContent = `${emotion}: `;
        container.appendChild(label);

        const progressBar = document.createElement('div');
        progressBar.className = 'progress';

        const progressBarFilled = document.createElement('div');
        progressBarFilled.className = 'progress-filled';
        progressBarFilled.style.width = `${(score * 100).toFixed(2)}%`;
        progressBarFilled.textContent = `${(score * 100).toFixed(2)}%`;

        progressBar.appendChild(progressBarFilled);
        container.appendChild(progressBar);

        emotionsDiv.appendChild(container);
    }

    // Display sentiment analysis results
    for (const [sentiment, score] of Object.entries(result.sentiment)) {
        const p = document.createElement('p');
        p.textContent = `${sentiment}: ${(score * 100).toFixed(2)}%`;
        sentimentDiv.appendChild(p);
    }
}

function displayAlert(message) {
    const alertMessage = document.getElementById('alert-message');
    alertMessage.textContent = message;
    alertMessage.classList.remove('hidden');
    alertMessage.classList.add('visible');
}

function hideAlert() {
    const alertMessage = document.getElementById('alert-message');
    alertMessage.classList.remove('visible');
    alertMessage.classList.add('hidden');
}

function clearResults() {
    document.getElementById('text-input').value = '';
    document.getElementById('emotions').innerHTML = '';
    document.getElementById('sentiment').innerHTML = '';
    document.getElementById('user-text-input').value = '';
    document.getElementById('ner-results').innerHTML = '';
    document.getElementById('topic-modeling-results').innerHTML = '';
    document.getElementById('ner-results-container').classList.add('hidden');
    document.getElementById('topic-modeling-results-container').classList.add('hidden');
    hideAlert();
}

function openHistoryModal() {
    displayHistory();
    document.getElementById('history-modal').style.display = 'flex';
}

function closeHistoryModal() {
    document.getElementById('history-modal').style.display = 'none';
}

function displayHistory() {
    const historyContent = document.getElementById('history-content');
    const history = JSON.parse(localStorage.getItem('history')) || { urls: [], texts: [] };
    historyContent.innerHTML = '';

    if (history.urls.length === 0 && history.texts.length === 0) {
        historyContent.innerHTML = '<p>No history available.</p>';
        return;
    }

    if (history.urls.length > 0) {
        const urlHeader = document.createElement('h3');
        urlHeader.textContent = 'URL History';
        historyContent.appendChild(urlHeader);

        history.urls.forEach(url => {
            const p = document.createElement('p');
            p.textContent = url;
            historyContent.appendChild(p);
        });
    }

    if (history.texts.length > 0) {
        const textHeader = document.createElement('h3');
        textHeader.textContent = 'Text History';
        historyContent.appendChild(textHeader);

        history.texts.forEach(text => {
            const p = document.createElement('p');
            p.textContent = text;
            historyContent.appendChild(p);
        });
    }
}

function storeUrlHistory(event) {
    const url = document.getElementById('url').value;
    const history = JSON.parse(localStorage.getItem('history')) || { urls: [], texts: [] };
    history.urls.push(url);
    localStorage.setItem('history', JSON.stringify(history));
}

function storeTextHistory(text) {
    const history = JSON.parse(localStorage.getItem('history')) || { urls: [], texts: [] };
    history.texts.push(text);
    localStorage.setItem('history', JSON.stringify(history));
}

function clearHistory() {
    localStorage.removeItem('history');
    displayHistory();
}

/* Feedback form functions */

function openFeedbackForm() {
    document.getElementById('feedback-modal').style.display = 'flex';
}

function closeFeedbackForm() {
    document.getElementById('feedback-modal').style.display = 'none';
}

async function submitFeedback(event) {
    event.preventDefault();
    const feedback = document.getElementById('feedback-input').value;

    if (feedback.trim() === '') {
        displayAlert('Feedback cannot be empty.');
        return;
    }

    const response = await fetch('/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ feedback: feedback })
    });

    if (response.ok) {
        closeFeedbackForm();
        document.getElementById('feedback-input').value = '';
        displayAlert('Thank you for your feedback!', 'success');
    } else {
        displayAlert('Failed to submit feedback. Please try again.');
    }
}

function displayAlert(message, type = 'error') {
    const alertMessage = document.getElementById('alert-message');
    alertMessage.textContent = message;
    alertMessage.className = 'alert visible ' + type;
    setTimeout(() => {
        alertMessage.classList.remove('visible');
        alertMessage.classList.add('hidden');
    }, 3000);
}

// function toggleGuide() {
//     var guideBox = document.getElementById('guide-box');
//     if (guideBox.style.width === '250px') {
//         guideBox.style.width = '0';
//     } else {
//         guideBox.style.width = '250px';
//     }
// }

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const questionInput = document.getElementById('question');
    const chatBox = document.getElementById('chat-box');
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotButton = document.getElementById('chatbot-button');
    const closeChatbotButton = document.getElementById('close-chatbot');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const question = questionInput.value.trim();
        if (question === '') return;

        // Display user's question
        const userMessage = document.createElement('div');
        userMessage.classList.add('user-message');
        userMessage.textContent = `You: ${question}`;
        chatBox.appendChild(userMessage);

        questionInput.value = '';

        // Fetch answer from server
        const response = await fetch('/get_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const result = await response.json();

        // Display bot's answer
        const botMessage = document.createElement('div');
        botMessage.classList.add('bot-message');
        botMessage.textContent = `Bot: ${result.answer}`;
        chatBox.appendChild(botMessage);

        if (!result.quit) {
            // Ask for feedback
            const feedbackMessage = document.createElement('div');
            feedbackMessage.classList.add('feedback-message');
            feedbackMessage.innerHTML = `
                <p>Was this answer helpful?</p>
                <button class="feedback-btn" id="yes-btn">Yes</button>
                <button class="feedback-btn" id="no-btn">No</button>
            `;
            chatBox.appendChild(feedbackMessage);

            document.getElementById('yes-btn').addEventListener('click', () => {
                chatBox.removeChild(feedbackMessage);
            });

            document.getElementById('no-btn').addEventListener('click', async () => {
                chatBox.removeChild(feedbackMessage);

                // Fetch similar questions from server
                const similarResponse = await fetch('/get_similar_questions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ similarity: result.similarity })
                });

                const similarResult = await similarResponse.json();
                const similarQuestions = similarResult.similar_questions;

                // Display similar questions
                const similarQuestionsMessage = document.createElement('div');
                similarQuestionsMessage.classList.add('similar-questions-message');
                similarQuestionsMessage.innerHTML = `
                    <p>Select the correct question:</p>
                    ${similarQuestions.map(q => `<button class="similar-question-btn">${q}</button>`).join('')}
                `;
                chatBox.appendChild(similarQuestionsMessage);

                // Handle selection of similar questions
                document.querySelectorAll('.similar-question-btn').forEach(btn => {
                    btn.addEventListener('click', async (event) => {
                        const selectedQuestion = event.target.textContent;
                        chatBox.removeChild(similarQuestionsMessage);

                        // Fetch the answer for the selected question
                        const selectedAnswerResponse = await fetch('/get_selected_answer', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ selected_question: selectedQuestion })
                        });

                        const selectedAnswerResult = await selectedAnswerResponse.json();

                        // Display the selected answer
                        const selectedAnswerMessage = document.createElement('div');
                        selectedAnswerMessage.classList.add('bot-message');
                        selectedAnswerMessage.textContent = `Bot: ${selectedAnswerResult.answer}`;
                        chatBox.appendChild(selectedAnswerMessage);
                    });
                });
            });
        }

        chatBox.scrollTop = chatBox.scrollHeight;

        // Check if quit
        if (result.quit) {
            questionInput.disabled = true;
            const quitMessage = document.createElement('div');
            quitMessage.classList.add('quit-message');
            quitMessage.textContent = "You have ended the chat session.";
            chatBox.appendChild(quitMessage);
        }
    });

    questionInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    chatbotButton.addEventListener('click', () => {
        chatbotContainer.classList.toggle('chatbot-hidden');
    });

    closeChatbotButton.addEventListener('click', () => {
        chatbotContainer.classList.add('chatbot-hidden');
    });
});


    document.addEventListener("DOMContentLoaded", function () {
        const username = sessionStorage.getItem('username');
        if (username) {
            const popupMessage = document.getElementById('popup-message');
            popupMessage.textContent = `Welcome ${username}`;
            popupMessage.style.display = 'block';
            setTimeout(() => {
                popupMessage.style.display = 'none';
                sessionStorage.removeItem('username'); // Remove username from session storage
            }, 2000);
        }
    });


    document.addEventListener("DOMContentLoaded", function () {
    const summarizeForm = document.getElementById("summarize-form");
    summarizeForm.addEventListener("submit", function () {
        document.getElementById("loading-spinner").style.display = "block";
    });

    window.addEventListener("pageshow", function (event) {
        if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
            document.getElementById("loading-spinner").style.display = "none";
        }
    });
});
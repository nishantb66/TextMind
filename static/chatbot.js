document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const questionInput = document.getElementById('question');
    const chatBox = document.getElementById('chat-box');
    const adminLoginBtn = document.getElementById('admin-login');
    const loginPopup = document.getElementById('login-popup');
    const loginForm = document.getElementById('login-form');
    const closeLoginPopupBtn = document.getElementById('close-login-popup');

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

                // Display similar questions
                const similarQuestionsMessage = document.createElement('div');
                similarQuestionsMessage.classList.add('similar-questions-message');
                similarQuestionsMessage.innerHTML = `
                    <p>Select the correct question:</p>
                    ${result.similar_questions.map(q => `<button class="similar-question-btn">${q}</button>`).join('')}
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

    adminLoginBtn.addEventListener('click', () => {
        loginPopup.style.display = 'block';
    });

    closeLoginPopupBtn.addEventListener('click', () => {
        loginPopup.style.display = 'none';
    });

    // loginForm.addEventListener('submit', async (event) => {
    //     event.preventDefault();
    //     const username = document.getElementById('username').value;
    //     const password = document.getElementById('password').value;

    //     if (username === 'admin' && password === 'admin1234') {
    //         window.location.href = '/admin';
    //     } else {
    //         alert('Invalid credentials');
    //     }
    // });
});
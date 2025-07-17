document.addEventListener('DOMContentLoaded', function() {
    let questions = [];
    let currentQuestionIndex = 0;
    let answers = {};
    
    const elements = {
        loading: document.getElementById('loading'),
        quizContainer: document.getElementById('quiz-container'),
        resultsContainer: document.getElementById('results-container'),
        errorContainer: document.getElementById('error-container'),
        questionsContainer: document.getElementById('questions-container'),
        quizForm: document.getElementById('quiz-form'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        submitBtn: document.getElementById('submit-btn'),
        progressBar: document.getElementById('progress-bar'),
        progressText: document.getElementById('progress-text'),
        errorMessage: document.getElementById('error-message')
    };
    
    // Load quiz questions
    loadQuizQuestions();
    
    async function loadQuizQuestions() {
        try {
            const response = await fetch('/recommendations/api/quiz/questions/');
            const data = await response.json();
            
            if (response.ok) {
                questions = data.questions;
                if (questions.length > 0) {
                    initializeQuiz();
                } else {
                    showError('No quiz questions available. Please contact support.');
                }
            } else {
                showError('Failed to load quiz questions. Please try again.');
            }
        } catch (error) {
            console.error('Error loading quiz questions:', error);
            showError('Network error. Please check your connection and try again.');
        }
    }
    
    function initializeQuiz() {
        elements.loading.classList.add('d-none');
        elements.quizContainer.classList.remove('d-none');
        
        renderQuestions();
        updateProgress();
        updateButtons();
    }
    
    function renderQuestions() {
        elements.questionsContainer.innerHTML = '';
        
        questions.forEach((question, index) => {
            const questionElement = createQuestionElement(question, index);
            elements.questionsContainer.appendChild(questionElement);
        });
        
        showQuestion(currentQuestionIndex);
    }
    
    function createQuestionElement(question, index) {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'quiz-question d-none';
        questionDiv.id = `question-${index}`;
        
        const questionTitle = document.createElement('h3');
        questionTitle.textContent = `${index + 1}. ${question.question_text}`;
        questionDiv.appendChild(questionTitle);
        
        const optionsContainer = document.createElement('div');
        
        switch (question.question_type) {
            case 'single_choice':
                optionsContainer.className = 'quiz-options';
                question.answer_options.forEach((option, optionIndex) => {
                    const optionDiv = createRadioOption(question.id, option, optionIndex);
                    optionsContainer.appendChild(optionDiv);
                });
                break;
                
            case 'multiple_choice':
                optionsContainer.className = 'quiz-options';
                question.answer_options.forEach((option, optionIndex) => {
                    const optionDiv = createCheckboxOption(question.id, option, optionIndex);
                    optionsContainer.appendChild(optionDiv);
                });
                break;
                
            case 'scale':
                optionsContainer.className = 'scale-options';
                for (let i = 1; i <= 5; i++) {
                    const scaleOption = createScaleOption(question.id, i);
                    optionsContainer.appendChild(scaleOption);
                }
                break;
                
            case 'text':
                const textInput = document.createElement('textarea');
                textInput.className = 'text-input';
                textInput.name = `question_${question.id}`;
                textInput.placeholder = 'Enter your answer...';
                textInput.rows = 3;
                textInput.addEventListener('input', handleTextInput);
                optionsContainer.appendChild(textInput);
                break;
        }
        
        questionDiv.appendChild(optionsContainer);
        return questionDiv;
    }
    
    function createRadioOption(questionId, option, optionIndex) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'quiz-option';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = `question_${questionId}`;
        radio.value = option;
        radio.id = `q${questionId}_${optionIndex}`;
        radio.addEventListener('change', handleRadioChange);
        
        const label = document.createElement('label');
        label.htmlFor = radio.id;
        label.textContent = option;
        
        optionDiv.appendChild(radio);
        optionDiv.appendChild(label);
        
        optionDiv.addEventListener('click', () => {
            radio.checked = true;
            handleRadioChange({ target: radio });
        });
        
        return optionDiv;
    }
    
    function createCheckboxOption(questionId, option, optionIndex) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'quiz-option';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = `question_${questionId}`;
        checkbox.value = option;
        checkbox.id = `q${questionId}_${optionIndex}`;
        checkbox.addEventListener('change', handleCheckboxChange);
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = option;
        
        optionDiv.appendChild(checkbox);
        optionDiv.appendChild(label);
        
        optionDiv.addEventListener('click', (e) => {
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
                handleCheckboxChange({ target: checkbox });
            }
        });
        
        return optionDiv;
    }
    
    function createScaleOption(questionId, value) {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'scale-option';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = `question_${questionId}`;
        radio.value = value;
        radio.id = `q${questionId}_scale_${value}`;
        radio.addEventListener('change', handleRadioChange);
        
        const label = document.createElement('label');
        label.htmlFor = radio.id;
        label.textContent = value;
        
        optionDiv.appendChild(radio);
        optionDiv.appendChild(label);
        
        optionDiv.addEventListener('click', () => {
            radio.checked = true;
            handleRadioChange({ target: radio });
        });
        
        return optionDiv;
    }
    
    function handleRadioChange(event) {
        const questionId = event.target.name.replace('question_', '');
        answers[questionId] = event.target.value;
        
        // Update visual selection
        const questionElement = document.getElementById(`question-${currentQuestionIndex}`);
        questionElement.querySelectorAll('.quiz-option, .scale-option').forEach(option => {
            option.classList.remove('selected');
        });
        event.target.closest('.quiz-option, .scale-option').classList.add('selected');
        
        updateButtons();
    }
    
    function handleCheckboxChange(event) {
        const questionId = event.target.name.replace('question_', '');
        
        if (!answers[questionId]) {
            answers[questionId] = [];
        }
        
        if (event.target.checked) {
            answers[questionId].push(event.target.value);
        } else {
            answers[questionId] = answers[questionId].filter(val => val !== event.target.value);
        }
        
        // Update visual selection
        event.target.closest('.quiz-option').classList.toggle('selected', event.target.checked);
        
        updateButtons();
    }
    
    function handleTextInput(event) {
        const questionId = event.target.name.replace('question_', '');
        answers[questionId] = event.target.value;
        updateButtons();
    }
    
    function showQuestion(index) {
        // Hide all questions
        document.querySelectorAll('.quiz-question').forEach(q => {
            q.classList.add('d-none');
            q.classList.remove('current');
        });
        
        // Show current question
        const currentQuestion = document.getElementById(`question-${index}`);
        if (currentQuestion) {
            currentQuestion.classList.remove('d-none');
            currentQuestion.classList.add('current');
        }
        
        updateProgress();
        updateButtons();
    }
    
    function updateProgress() {
        const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
        elements.progressBar.style.width = `${progress}%`;
        elements.progressText.textContent = `${currentQuestionIndex + 1} / ${questions.length}`;
    }
    
    function updateButtons() {
        elements.prevBtn.disabled = currentQuestionIndex === 0;
        
        const isLastQuestion = currentQuestionIndex === questions.length - 1;
        const currentQuestionId = questions[currentQuestionIndex].id;
        const hasAnswer = answers[currentQuestionId] !== undefined && answers[currentQuestionId] !== '';
        
        if (isLastQuestion) {
            elements.nextBtn.classList.add('d-none');
            elements.submitBtn.classList.remove('d-none');
            elements.submitBtn.disabled = !hasAnswer;
        } else {
            elements.nextBtn.classList.remove('d-none');
            elements.submitBtn.classList.add('d-none');
            elements.nextBtn.disabled = !hasAnswer;
        }
    }
    
    function nextQuestion() {
        if (currentQuestionIndex < questions.length - 1) {
            currentQuestionIndex++;
            showQuestion(currentQuestionIndex);
        }
    }
    
    function previousQuestion() {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            showQuestion(currentQuestionIndex);
        }
    }
    
    async function submitQuiz() {
        try {
            elements.submitBtn.disabled = true;
            elements.submitBtn.textContent = 'Submitting...';
            
            const response = await fetch('/recommendations/api/quiz/submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ answers })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                elements.quizContainer.classList.add('d-none');
                elements.resultsContainer.classList.remove('d-none');
            } else {
                showError(data.error || 'Failed to submit quiz. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting quiz:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            elements.submitBtn.disabled = false;
            elements.submitBtn.textContent = 'Submit Quiz';
        }
    }
    
    function showError(message) {
        elements.loading.classList.add('d-none');
        elements.quizContainer.classList.add('d-none');
        elements.resultsContainer.classList.add('d-none');
        elements.errorContainer.classList.remove('d-none');
        elements.errorMessage.textContent = message;
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Event listeners
    elements.prevBtn.addEventListener('click', previousQuestion);
    elements.nextBtn.addEventListener('click', nextQuestion);
    elements.quizForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitQuiz();
    });
});
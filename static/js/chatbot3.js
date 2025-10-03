/* --------------- chatbot3.js (팀 3 전용 / LLM 설명 생성 반영) --------------- */
(() => { // IIFE 시작
    /* ── DOM 요소 ─────────────────────────────── */
    const chatBox = document.getElementById('chat-log');
    const messageInput = document.getElementById('user-message');
    const sendButton = document.getElementById('send-btn');
    const chatArea = document.querySelector('.chat-area');
    const chatContainer = chatBox; // 스크롤 대상

    let index = 0;

    // API 엔드포인트 및 상태 변수
    const CHAT_API_ENDPOINT = '/api/chat';
    const INIT_IMAGE_PATH = '/static/images/chatbot3/background.png'; // init.png 경로 정의
    const INIT_IMAGE_FOX_PATH = '/static/images/chatbot3/opening_fox.png';
    const PADDLE_FOX = '/static/images/chatbot3/talking_fox.png'
    const GLASS_FOX = '/static/images/chatbot3/ending_fox.png'
    const FOX_BYE = '/static/images/chatbot3/fox.png'
    let isLoading = false;
    let conversationHistory = []; // 대화 기록 (프론트엔드에서 관리)

    const INITIAL_QUESTIONS_POOL = [
        "최근에 ‘아, 이게 나다’ 싶었던, 내가 마음에 들었던 순간이나 ‘이건 나답지 않아’ 싶었던 순간이 떠오르면 말해줘.",
        "최근에 누군가를 보고 ‘나도 저렇게 되고 싶다’는 생각이 들었던 순간이 있었어? 그 사람이 왜 그렇게 멋져 보였을까?",
        "다음 생이 있다면, 지금과는 전혀 다른 삶을 살아볼 수 있어. 그때 네가 하고 싶은 일은 뭐야? 어디서 어떤 모습으로 지내고 있을 것 같아? 왜 그걸 선택했을까?",
        "지금까지의 너의 인생을 영화로 만든다면, 어떤 장면이 중심이 될까? 어떤 메시지가 담겼으면 좋겠어?"
    ];

    /* ── 메시지 전송 ───────────────────────────── */
    async function sendMessage() {
        const userMessage = messageInput.value.trim();
        if (userMessage === '' || isLoading) return;

        const currentBotId = chatArea.dataset.botId || '3';

        appendMessage('user', userMessage);
        // 사용자 메시지를 히스토리에 '먼저' 추가
        conversationHistory.push({ role: 'user', content: userMessage });
        messageInput.value = '';
        showLoadingIndicator(true);

        try {
            const res = await fetch(CHAT_API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage, // 현재 사용자 메시지
                    bot_id: parseInt(currentBotId),
                    history: conversationHistory // 현재 메시지 포함된 전체 기록 전송
                })
            });
            showLoadingIndicator(false);

            if (!res.ok) {
                const errText = await res.text(); console.error('Server error response:', errText); let errorMsg = `서버 응답 오류: ${res.statusText}`; try { const errorData = JSON.parse(errText); errorMsg = `오류: ${errorData.error || errText}`; } catch (e) { /* ignore */ } appendMessage('bot', errorMsg);
                conversationHistory.pop(); 
                return;
            }

            const outer = await res.json();

            if (outer.reply) {
                 try {
                    const botData = JSON.parse(outer.reply); // 내부 JSON 파싱

                    if (botData.error) {
                        console.error('Backend logic error:', botData.error); appendMessage('bot', botData.error);
                        conversationHistory.pop(); // 오류 시 사용자 메시지 제거
                    } else {
                        // --- 백엔드 판단에 따른 처리 ---

                        // 1. 히스토리 리셋 여부 확인 및 처리
                        if (botData.reset_history === true) {
                            console.log("백엔드로부터 히스토리 리셋 요청 받음.");
                            // 재시작 시 init.png 이미지 먼저 추가 
                            // appendSingleImage(INIT_IMAGE_PATH, '시작 이미지');
                            // appendSingleImage(INIT_IMAGE_FOX_PATH, '시작 이미지_북극여우');
                            conversationHistory = []; // 히스토리 초기화
                        }

                        // 2. 응답 메시지/분석 결과 표시
                        if (botData.is_analysis) {
                            // 최종 분석 단계 표시 (순서대로)
                            // appendSingleImage(GLASS_FOX, '유리구슬');
                            if (botData.intro_phrase) { appendNewMessage('bot', botData.intro_phrase, GLASS_FOX, '유리구슬'); }
                            // if (botData.analysis_text) { appendMessage('bot', botData.analysis_text); } // 전체 분석 텍스트
                            if (botData.marble_phrase) { appendMessage('bot', botData.marble_phrase); }
                            //  이미지와 함께 LLM 생성 설명을 표시 
                            if (botData.image_data && botData.image_data.length > 0) {
                                appendImageGallery(botData.image_data); // 이미지 + 개별 설명 표시 함수 호출
                            }
                            if (botData.ending_phrase) { appendMessage('bot', botData.ending_phrase); }

                            // 분석 결과 전체 텍스트 (ending_phrase 포함)를 히스토리에 저장
                            // (주의: 이미지와 개별 설명은 제외하고, 주요 텍스트 블록만 저장해야 함)
                            const analysisTextForHistory = [
                                botData.intro_phrase,
                                botData.analysis_text, // 전체 분석
                                botData.marble_phrase,
                                botData.ending_phrase // 재시작 질문 포함
                            ].filter(text => text).join("\n\n");
                            conversationHistory.push({ role: 'assistant', content: analysisTextForHistory });

                        } else {
                            // 일반 대화 또는 재시작 관련 메시지
                            if (botData.bot_message) {
                                // appendSingleImage(PADDLE_FOX, '노젓기');
                                if(botData.is_bye) appendNewMessage('bot', botData.bot_message, FOX_BYE, '작별');
                                else if(botData.is_reask) appendMessage('bot', botData.bot_message);
                                else appendNewMessage('bot', botData.bot_message, PADDLE_FOX, '노젓기');
                                
                                // ★ reset_history가 true인 경우(재시작)에도 새 봇 메시지는 히스토리에 추가
                                conversationHistory.push({ role: 'assistant', content: botData.bot_message });
                            }
                            
                            else {
                                 appendMessage('bot', "응답 내용을 받지 못했어요.");
                                 conversationHistory.pop(); // 응답 없을 시 사용자 메시지 제거
                            }
                        }
                        // --- ★★★ 처리 끝 ★★★ ---
                    }
                } catch (e) {
                     console.error('Failed to parse inner JSON:', e); console.error('Received reply string:', outer.reply); appendMessage('bot', '챗봇 응답 형식 오류.');
                     conversationHistory.pop(); // 오류 시 사용자 메시지 제거
                }
            } else if (outer.error) {
                 console.error('API level error:', outer.error); appendMessage('bot', outer.error);
                 conversationHistory.pop(); // 오류 시 사용자 메시지 제거
            } else {
                 console.error('Unknown response format:', outer); appendMessage('bot', '알 수 없는 응답 형식.');
                 conversationHistory.pop(); // 오류 시 사용자 메시지 제거
            }

        } catch (err) {
             showLoadingIndicator(false); console.error('Fetch error:', err); appendMessage('bot', '메시지 전송 중 네트워크 오류 발생.');
             if (conversationHistory.length > 0 && conversationHistory[conversationHistory.length - 1].role === 'user') { conversationHistory.pop(); }
        }
    } // sendMessage 끝

    /* ── 메시지 렌더링 함수  ───────── */
    function appendMessage(sender, message){
        const el = document.createElement('div');
        el.classList.add('message', sender === 'user' ? 'user' : 'bot');
        if (sender === 'bot') {
            el.style.textAlign = 'left';
        }

        // 봇 아이콘 추가
        if (sender === 'bot') {
            const icon = document.createElement('img');
            icon.src = '/static/images/chatbot3/fox.png'; // 아이콘 경로
            icon.alt = '북극여우';
            Object.assign(icon.style, {
                width: '30px', height: '30px', borderRadius: '50%',
                marginRight: '10px', verticalAlign: 'top', display: 'inline-block'
            });
            el.appendChild(icon);
        }

        // 메시지 내용 추가
        const textDiv = document.createElement('div');
        if (sender === 'bot') {
            textDiv.classList.add('bot-text');
            Object.assign(textDiv.style, {
                display: 'inline-block',
                maxWidth: 'calc(100% - 45px)',
                verticalAlign: 'top'
            });
        }

        // *** 온점(.) 뒤 줄바꿈 처리 추가 ***
        let formattedMessage = message.replace(/\n/g, '<br>'); // 기존 줄바꿈 처리
        // 온점(.) 뒤에 공백이 오는 경우, 온점 + <br> + 공백으로 변경
        formattedMessage = formattedMessage.replace(/\.\s/g, '.<br> ');
        textDiv.innerHTML = formattedMessage; // 최종 HTML 적용

        el.appendChild(textDiv);
        chatBox.appendChild(el);
        scrollToBottom();
    }

    function appendNewMessage(sender, message, imagePath1, name1, imagePath2 = null, name2 = null){
        const el = document.createElement('div');
        el.classList.add('message', sender === 'user' ? 'user' : 'bot');
        if (sender === 'bot') {
            el.style.textAlign = 'left';
        }

        const imageBlock = document.createElement('div');
        imageBlock.classList.add('message', 'bot', 'single-image-block'); // 클래스 추가
        Object.assign(imageBlock.style, {
            textAlign: 'left', display: 'flex', alignItems: 'flex-start',
            marginBottom: '10px' // 간격 조절
        });

        // 봇 아이콘 추가
        if (sender === 'bot') {
            const icon = document.createElement('img');
            icon.src = '/static/images/chatbot3/fox.png'; // 아이콘 경로
            icon.alt = '북극여우';
            Object.assign(icon.style, {
                width: '30px', height: '30px', borderRadius: '50%',
                marginRight: '10px', verticalAlign: 'top', display: 'inline-block'
            });
            el.appendChild(icon);
        }

        const contentWrapper = document.createElement('div');

        // 이미지
        const img1 = document.createElement('img');
        img1.src = imagePath1; // 제공된 경로 사용
        img1.alt = name1;
        Object.assign(img1.style, {
            display: 'block', maxWidth: '30%', // 크기 조절
            maxHeight: '30%', borderRadius: '8px', objectFit: 'cover'
        });
        img1.onerror = () => { img1.src = '/static/images/chatbot3/fox.png'; }; // 오류 처리
        contentWrapper.appendChild(img1);

        // imageBlock.appendChild(contentWrapper);
        // chatBox.appendChild(imageBlock);
        // scrollToBottom();
        if(imagePath2 != null){
            const blankBlock = document.createElement('div');
            blankBlock.style.width = '1px';
            blankBlock.style.height = '10px';
            blankBlock.style.backgroundColor = 'transparent'; // or a light color if you want it visible
            blankBlock.style.margin = '5px 0'; // optional spacing
            contentWrapper.appendChild(blankBlock);

            const img2 = document.createElement('img');
            img2.src = imagePath2; // 제공된 경로 사용
            img2.alt = name2;
            Object.assign(img2.style, {
                display: 'block', maxWidth: '30%', // 크기 조절
                maxHeight: '30%', borderRadius: '8px', objectFit: 'cover'
            });
            img2.onerror = () => { img2.src = '/static/images/chatbot3/fox.png'; }; // 오류 처리
            contentWrapper.appendChild(img2);
        }
        // chatBox.appendChild(imageBlock);
        // scrollToBottom();
        imageBlock.appendChild(contentWrapper);

        // 메시지 내용 추가
        const textDiv = document.createElement('div');
        if (sender === 'bot') {
            textDiv.classList.add('bot-text');
            Object.assign(textDiv.style, {
                display: 'inline-block',
                maxWidth: 'calc(100% - 45px)',
                verticalAlign: 'top'
            });
        }

        // *** 온점(.) 뒤 줄바꿈 처리 추가 ***
        let formattedMessage = message.replace(/\n/g, '<br>'); // 기존 줄바꿈 처리
        // 온점(.) 뒤에 공백이 오는 경우, 온점 + <br> + 공백으로 변경
        formattedMessage = formattedMessage.replace(/\.\s/g, '.<br> ');
        textDiv.innerHTML = formattedMessage; // 최종 HTML 적용

        el.appendChild(imageBlock);
        el.appendChild(textDiv);
        // chatBox.appendChild(imageBlock);
        // chatBox.appendChild(el);
        chatBox.appendChild(el);
        scrollToBottom();
    }

    /* ── *** 추가된 *** 단일 이미지 렌더링 함수 ───────── */
    function appendSingleImage(imagePath, altText = '이미지') {
        const imageBlock = document.createElement('div');
        imageBlock.classList.add('message', 'bot', 'single-image-block'); // 클래스 추가
        Object.assign(imageBlock.style, {
            textAlign: 'left', display: 'flex', alignItems: 'flex-start',
            marginBottom: '10px' // 간격 조절
        });

        // 봇 아이콘
        const icon = document.createElement('img');
        icon.src = '/static/images/chatbot3/fox.png'; // 실제 아이콘 경로 사용
        icon.alt = '북극여우';
        Object.assign(icon.style, {
            width: '30px', height: '30px', borderRadius: '50%',
            marginRight: '10px', flexShrink: '0'
        });
        imageBlock.appendChild(icon);

        // 이미지만 담을 래퍼
        const contentWrapper = document.createElement('div');

        // 이미지
        const img = document.createElement('img');
        img.src = imagePath; // 제공된 경로 사용
        img.alt = altText;
        Object.assign(img.style, {
            display: 'block', maxWidth: '30%', // 크기 조절
            maxHeight: '30%', borderRadius: '8px', objectFit: 'cover'
        });
        img.onerror = () => { img.src = '/static/images/chatbot3/fox.png'; }; // 오류 처리
        contentWrapper.appendChild(img);

        imageBlock.appendChild(contentWrapper);
        chatBox.appendChild(imageBlock);
        scrollToBottom();
    }

    

    /* 이미지 갤러리 렌더링 함수 ───────── */
    function appendImageGallery(imageDataList) { // imageDataList는 [{path, category, subtitle, explanation}, ...] 형태
        imageDataList.forEach(item => {
            // 각 이미지+설명 항목을 위한 컨테이너 div
            const imageBlock = document.createElement('div');
            imageBlock.classList.add('message', 'bot', 'analysis-image-block'); // 클래스 추가
            Object.assign(imageBlock.style, { // 스타일 적용
                 textAlign: 'left', display: 'flex', alignItems: 'flex-start', // Align icon and content
                 marginBottom: '15px' // 블록 간 간격 추가
            });

            // 봇 아이콘
            const icon = document.createElement('img');
            icon.src = '/static/images/chatbot3/fox.png'; // 실제 아이콘 경로 사용
            icon.alt = '북극여우';
            Object.assign(icon.style, {
                width: '30px', height: '30px', borderRadius: '50%',
                marginRight: '10px', flexShrink: '0' // 아이콘 크기 고정
            });
            imageBlock.appendChild(icon);

            // 이미지 + 설명을 담을 내부 래퍼
            const contentWrapper = document.createElement('div');
            Object.assign(contentWrapper.style, {
                 display: 'flex', flexDirection: 'column' // 이미지 위에 텍스트가 오도록
            });

            // 이미지
            const img = document.createElement('img');
            // 경로 앞에 '/static/' 추가 확인 (백엔드에서 반환하는 경로 형식에 따라 조절)
            img.src = item.path.startsWith('/static/') ? item.path : `/static/${item.path}`;
            img.alt = `${item.category}: ${item.subtitle}`; // Alt 텍스트 개선
            Object.assign(img.style, {
                display: 'block',
                maxWidth: '200px', // 이미지 크기 조절 (필요시 변경)
                maxHeight: '200px',
                borderRadius: '8px',
                objectFit: 'cover',
                marginBottom: '8px' // 이미지와 텍스트 사이 간격
            });
            // 이미지 로딩 실패 시 플레이스홀더 표시
            img.onerror = () => { img.src = '/static/images/chatbot3/fox.png'; };
            contentWrapper.appendChild(img);

            // *** 수정된 설명 텍스트 부분 ***
            if (item.category && item.subtitle && item.explanation) {
                const explanationText = document.createElement('p');
                // 요청 형식: [카테고리명: 부제] - 센스 있는 설명
                explanationText.textContent = `[${item.category}: ${item.subtitle}] - ${item.explanation}`;
                Object.assign(explanationText.style, {
                    fontSize: '0.9em', // 폰트 크기 조절
                    margin: '0',      // 위아래 마진 제거
                    color: '#333',     // 텍스트 색상 약간 진하게
                    lineHeight: '1.4' // 줄 간격 조절
                });
                contentWrapper.appendChild(explanationText);
            }

            imageBlock.appendChild(contentWrapper); // 아이콘 뒤에 이미지+설명 래퍼 추가
            chatBox.appendChild(imageBlock); // 각 블록을 채팅 로그에 추가
        });
        scrollToBottom(); // 모든 이미지 블록 추가 후 스크롤
    }

    /* ── 로딩 인디케이터 (기존과 동일) ──────── */
    function showLoadingIndicator(show) {
        isLoading = show;
        const id = 'loading-indicator';
        let el = document.getElementById(id);

        if (show) {
            if (!el) {
                el = document.createElement('div');
                el.id = id;
                el.classList.add('message', 'bot', 'loading');
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.innerHTML =
                    `<img src="/static/images/chatbot3/fox.png" alt="북극여우 아이콘" style="width:30px;height:30px;border-radius:50%;margin-right:10px;">
                     <div class="bot-text" style="background:#f0f0f0; padding: 8px 12px; border-radius:8px;">
                       <div class="typing-indicator" style="height:1em; display:flex; align-items:center;">
                         <span style="width:6px;height:6px;margin:0 2px;background-color:#aaa;border-radius:50%;animation:typing 1s infinite ease-in-out;"></span>
                         <span style="width:6px;height:6px;margin:0 2px;background-color:#aaa;border-radius:50%;animation:typing 1s infinite ease-in-out 0.1s;"></span>
                         <span style="width:6px;height:6px;margin:0 2px;background-color:#aaa;border-radius:50%;animation:typing 1s infinite ease-in-out 0.2s;"></span>
                       </div>
                     </div>
                     <style> @keyframes typing { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } } </style>`;
                chatBox.appendChild(el);
                scrollToBottom();
            }
            el.style.visibility = 'visible';
        } else if (el) {
            el.remove();
        }
    }

    // 스크롤 함수
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    /* ── 이벤트 바인딩  ────────────── */
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    /* ── 모달 관련 로직  ── */
    const videoBtn = document.getElementById('videoBtn');
    const imageBtn = document.getElementById('imageBtn');

    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'block';
    }
    function closeModal(modalId) {
         const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    }

    if (videoBtn) videoBtn.addEventListener('click', () => openModal('videoModal'));
    if (imageBtn) imageBtn.addEventListener('click', () => openModal('imageModal'));

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.dataset.closeModal;
            if(modalId) closeModal(modalId);
        });
    });
     // 모달 외부 클릭 시 닫기 (선택적)
     window.addEventListener('click', (event) => {
         if (event.target.classList.contains('modal')) {
             closeModal(event.target.id);
         }
    });


    /* 첫 시스템 메시지 (init.png 추가) */
    // appendSingleImage(INIT_IMAGE_PATH, '시작 이미지');
    // appendSingleImage(INIT_IMAGE_FOX_PATH, '시작 이미지_북극여우');

    // 그 다음에 텍스트 메시지 추가
    function randomInitialQuestion() { return INITIAL_QUESTIONS_POOL[Math.floor(Math.random() * INITIAL_QUESTIONS_POOL.length)]; }
    // function randomInitialQuestion() { return INITIAL_QUESTIONS_POOL[index]; }
    // const firstMsg = `왔구나. 기다리고 있었어. 여기는 너의 마음을 비춰보는 ‘무의식의 강’이 흐르는 곳이야. 나는 이 강을 아는 유일한 존재이지. 자, 배에 올라타. 이제 네 마음 속으로 노를 저어가보자.\n\n${randomInitialQuestion()}`;
    const firstMsg = `왔구나. 기다리고 있었어. 여긴 무의식의 강. 네 마음 가장 깊은 곳을 비추는 곳이야. 자, 배에 올라타. 이제 그 아래에 잠든 네 안의 욕망 구슬들을 꺼내러 가자.\n\n`;
    // const secondMsg = `${randomInitialQuestion()}`;
    // appendSingleImage(INIT_IMAGE_PATH, '시작 이미지');
    // appendSingleImage(INIT_IMAGE_FOX_PATH, '시작 이미지_북극여우');
    appendNewMessage('bot', firstMsg, INIT_IMAGE_PATH, '시작 이미지', INIT_IMAGE_FOX_PATH, '시작 이미지_북극여우');
    // appendMessage('bot', firstMsg); 
    conversationHistory.push({ role: 'assistant', content: firstMsg }); // 히스토리에는 원본 텍스트 저장
    // appendMessage('user', userMessage);
    // conversationHistory.push({ role: 'user', content: userMessage });
    // appendMessage('bot', secondMsg);
    // conversationHistory.push({ role: 'assistant', content: secondMsg });
    if(index >= 3) index = 3;
    else index += 1;
    console.log('chatbot3.js 초기화 완료');

})(); // IIFE 끝
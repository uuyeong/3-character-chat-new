// chat-area에서 bot_id와 bot_image_url 정보 꺼내기
const chatArea = document.querySelector('.chat-area');
const botId = chatArea.dataset.botId;

// 주요 DOM 요소
const chatLog = document.getElementById('chat-log');
const userMessageInput = document.getElementById('user-message');
const sendBtn = document.getElementById('send-btn');
const videoBtn = document.getElementById('videoBtn');
const imageBtn = document.getElementById('imageBtn');

// 메시지 전송 함수
async function sendMessage() {
  const message = userMessageInput.value.trim();
  if (!message) return;

  appendMessage('user', message);
  userMessageInput.value = '';

  const loadingElem = document.createElement('div');
  loadingElem.classList.add('message', 'bot', 'loading');

  const loadingText = document.createElement('div');
  loadingText.classList.add('bot-text');
  loadingText.textContent = "...";

  loadingElem.appendChild(loadingText);
  chatLog.appendChild(loadingElem);
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_id: botId, message: message })
    });

    chatLog.removeChild(loadingElem);

    const data = await response.json();

    if (data.text || data.type) {
      appendBotMessage(data);
    } else if (data.reply) {
      appendMessage('bot', data.reply);
    } else if (data.error) {
      appendMessage('bot', 'Error: ' + data.error);
    }
  } catch (err) {
    if (chatLog.contains(loadingElem)) {
      chatLog.removeChild(loadingElem);
    }
    appendMessage('bot', 'Error: 요청 실패');
    console.error(err);
  }
}

// 사용자 / 챗봇 메시지 기본 출력
function appendMessage(sender, text) {
  const messageElem = document.createElement('div');
  messageElem.classList.add('message', sender);

  if (sender === 'user') {
    messageElem.textContent = text;
  } else {
    const botImg = document.createElement('img');
    botImg.classList.add('bot-big-img');
    botImg.alt = "챗봇 이미지";

    const messageText = document.createElement('div');
    messageText.classList.add('bot-text');
    messageText.textContent = text;

    messageElem.appendChild(botImg);
    messageElem.appendChild(messageText);
  }

  chatLog.appendChild(messageElem);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function appendBotMessage(data) {
  const messageElem = document.createElement('div');
  messageElem.classList.add('message', 'bot');

  const messageContainer = document.createElement('div');
  messageContainer.classList.add('bot-content');

  // === intro 구조 ===
  if (data.type === 'intro' && typeof data.text === 'object') {
    const { title, description, commands } = data.text;

    const titleDiv = document.createElement('div');
    titleDiv.classList.add('bot-text');
    titleDiv.innerText = title;
    messageContainer.appendChild(titleDiv);

    const desc = document.createElement('p');
    desc.textContent = description;
    messageContainer.appendChild(desc);

    const ul = document.createElement('ul');
    commands.forEach(cmd => {
      const li = document.createElement('li');
      li.textContent = `${cmd.label}: ${cmd.desc}`;
      ul.appendChild(li);
    });
    messageContainer.appendChild(ul);
  }

  // === 엔딩 ===
  else if (data.type === 'ending') {
    if (data.choice_text) {
      const choiceMsg = document.createElement('div');
      choiceMsg.classList.add('bot-text');
      choiceMsg.textContent = data.choice_text;
      messageContainer.appendChild(choiceMsg);
    }

    const resultText = document.createElement('div');
    resultText.classList.add('bot-text');
    resultText.textContent = data.text;
    messageContainer.appendChild(resultText);

    if (data.final_stats) {
      const statList = document.createElement('ul');
      Object.entries(data.final_stats).forEach(([major, value]) => {
        const li = document.createElement('li');
        li.textContent = `${major}: ${value}`;
        statList.appendChild(li);
      });
      messageContainer.appendChild(statList);
    }
  }

  // === 스토리 ===
  else if (data.type === 'story') {
    const storyText = document.createElement('div');
    storyText.classList.add('bot-text');
    storyText.textContent = data.text;
    messageContainer.appendChild(storyText);

    if (data.event) {
      const eventDiv = document.createElement('div');
      eventDiv.classList.add('event-container');

      const eventTitle = document.createElement('h3');
      eventTitle.textContent = data.event.name || '이벤트';
      eventDiv.appendChild(eventTitle);

      const eventDesc = document.createElement('p');
      eventDesc.textContent = data.event.description;
      eventDiv.appendChild(eventDesc);

      if (data.event.choices && data.event.choices.length > 0) {
        const choicesList = document.createElement('ul');
        choicesList.classList.add('choices-list');

        data.event.choices.forEach((choice, index) => {
          const choiceItem = document.createElement('li');
          choiceItem.textContent = `${index + 1}. ${choice}`;
          choiceItem.addEventListener('click', () => {
            userMessageInput.value = `/선택 ${index + 1}`;
            sendMessage();
          });
          choiceItem.style.cursor = 'pointer';
          choicesList.appendChild(choiceItem);
        });

        eventDiv.appendChild(choicesList);
      }

      messageContainer.appendChild(eventDiv);
    }
  }

  // === 도움말 ===
  else if (data.type === 'help') {
    const helpTitle = document.createElement('h4');
    helpTitle.textContent = '도움말 명령어 목록';
    messageContainer.appendChild(helpTitle);

    const commandList = document.createElement('ul');
    data.commands.forEach(cmd => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.textContent = cmd.command;
      btn.title = cmd.description;
      btn.classList.add('command-btn');
      btn.addEventListener('click', () => {
        userMessageInput.value = cmd.example;
        sendMessage();
      });
      li.appendChild(btn);
      li.innerHTML += ` - ${cmd.description}`;
      commandList.appendChild(li);
    });
    messageContainer.appendChild(commandList);
  }

  // === 상태 ===
  else if (data.type === 'status') {
    const statusTitle = document.createElement('h4');
    statusTitle.textContent = '현재 상태';
    messageContainer.appendChild(statusTitle);

    const currentEvent = document.createElement('p');
    currentEvent.innerHTML = `<strong>현재 이벤트:</strong> ${data.current_event} (${data.current_choice_made ? '선택 완료' : '선택 필요'})`;
    messageContainer.appendChild(currentEvent);

    const statsTitle = document.createElement('h4');
    statsTitle.textContent = '전공 스탯';
    messageContainer.appendChild(statsTitle);

    const statsList = document.createElement('ul');
    const maxStat = Math.max(...Object.values(data.major_stats));
    Object.entries(data.major_stats).forEach(([major, value]) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="stat-row">
          <span class="stat-major">${major}</span>
          <div class="stat-bar">
            <div class="stat-bar-fill" style="width: ${maxStat > 0 ? (value / maxStat * 100) : 0}%"></div>
          </div>
        </div>
      `;
      statsList.appendChild(li);
    });
    messageContainer.appendChild(statsList);

    const choiceTitle = document.createElement('h4');
    choiceTitle.textContent = '선택 내역';
    messageContainer.appendChild(choiceTitle);

    const choiceList = document.createElement('ul');
    Object.entries(data.choices_history).forEach(([event, info]) => {
      const li = document.createElement('li');
      li.textContent = `${event}: ${info.choice}`;
      choiceList.appendChild(li);
    });
    messageContainer.appendChild(choiceList);
  }

  // === 일반 메시지 ===
  else if (data.text) {
    const messageText = document.createElement('div');
    messageText.classList.add('bot-text');
    messageText.textContent = data.text;
    messageContainer.appendChild(messageText);
  }

  // === 이미지 출력 공통 ===
  if (data.image_url) {
    const imageElem = document.createElement('img');
    imageElem.src = data.image_url;
    imageElem.alt = "관련 이미지";
    // 이미지 크기 제한 설정 (핵심 수정 부분)
    imageElem.classList.add('chat-image');
    imageElem.style.width = '50%'; 
    imageElem.style.display = 'block';
    imageElem.style.margin = '10px auto';
    messageContainer.appendChild(imageElem);
  }

  // === 감정 분석 ===
  if (data.emotion) {
    // 감정 이미지만 표시하고 텍스트 태그는 생략
    if (data.emotion.image_url) {
      const emotionImg = document.createElement('img');
      emotionImg.src = data.emotion.image_url;
      emotionImg.alt = `${data.emotion.dominant_emotion} 감정`;
      emotionImg.classList.add('emotion-image');
      emotionImg.style.width = '50%';
      emotionImg.style.display = 'block';
      emotionImg.style.margin = '10px auto';
      messageContainer.appendChild(emotionImg);
    }
  }
  // === 힌트 ===
  if (data.hint) {
    const hintDiv = document.createElement('div');
    hintDiv.classList.add('hint-message');
    hintDiv.textContent = data.hint;
    messageContainer.appendChild(hintDiv);
  }

  messageElem.appendChild(messageContainer);
  chatLog.appendChild(messageElem);
  chatLog.scrollTop = chatLog.scrollHeight;
}



// 전송 관련 이벤트
userMessageInput.addEventListener('keyup', (event) => {
  if (event.key === 'Enter') sendMessage();
});
sendBtn.addEventListener('click', sendMessage);

// 모달 제어
function openModal(modalId) {
  document.getElementById(modalId).style.display = 'block';
}
function closeModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
}
videoBtn.addEventListener('click', () => openModal('videoModal'));
imageBtn.addEventListener('click', () => openModal('imageModal'));
document.querySelectorAll('.modal-close').forEach(btn => {
  btn.addEventListener('click', () => {
    const modal = btn.closest('.modal');
    closeModal(modal.id);
  });
});

// 첫 진입 환영 메시지
// 첫 진입 환영 메시지
// 첫 진입 환영 메시지
// 첫 진입 환영 메시지
// 첫 진입 환영 메시지 - 다음 코드로 변경
// 첫 진입 환영 메시지 - 다음 코드로 변경

if (botId == 4) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message bot';
  msgDiv.innerHTML = `
    <div class="bot-content">
      <div class="bot-text">안녕하세요 선배님! (✨꾸벅) 저, 이번에 자율전공학부로 입학한 새내기 이알로예요! 어디서 많이 본 것 같다구요…? 헤헤, 사실 학교에 좀 오래 있었거든요. (소근소근) 처음이라 모르는 것도 많고, 캠퍼스도 너무 넓고 신기해서… 혹시 괜찮으시다면, 선배님께 이것저것 여쭤봐도 될까요?<br>
      🗺<strong>캠퍼스 투어부터 시작해서</strong><br>
      📝<strong>수강신청 고민 상담이나</strong><br>
      🔖<strong>시험기간 꿀팁 전수</strong><br>
      아니면 그냥 수다도 좋아요!<br>
      오늘부터 제… 서강 생활 생존 멘토, 해주실 수 있나요 선배님? (ˊᵕˋ)੭</div>
      <p>💡 챗봇 사용법</p>
      <ul>
        <li>/스토리: 알로스의 대학 생활을 함께 진행해요!</li>
        <li>/상태: 지금까지의 선택과 전공 스탯을 볼 수 있어요</li>
        <li>/도움말: 사용 가능한 명령어들을 안내해드려요</li>
      </ul>
      <p style="color: #9264d1; font-weight: bold; margin-top: 15px; text-align: center; padding: 10px; border: 2px dashed #9264d1; border-radius: 8px;">
👉 <strong>"/스토리"</strong> 명령어를 입력하여 알로스의 대학 생활 스토리를 시작해보세요!
      </p>
    </div>
  `;
  chatLog.appendChild(msgDiv);

  // 서버에도 /start 전송
  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bot_id: parseInt(botId), message: "/start" })
  });
}
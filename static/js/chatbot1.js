console.log("chatbot1.js 시작");

// URL 쿼리 파라미터에서 사용자 이름 추출
const urlParams = new URLSearchParams(window.location.search);
const username = urlParams.get("username") || "";
console.log("추출된 username:", username);

// chat-area, chat-log, user-message, send-btn 등 주요 DOM 요소들이 있는지 확인
const chatArea = document.querySelector('.chat-area');
if (!chatArea) {
  console.error("chat-area 요소를 찾을 수 없습니다.");
} else {
  console.log("chat-area 로드됨:", chatArea);
}

const botId = chatArea ? chatArea.dataset.botId : null;
const botImageUrl = chatArea ? chatArea.dataset.botImageUrl : null;  // 기본 이미지 (fallback 용)

const chatLog = document.getElementById('chat-log');
if (!chatLog) {
  console.error("chat-log 요소를 찾을 수 없습니다.");
} else {
  console.log("chat-log 로드됨:", chatLog);
}

const userMessageInput = document.getElementById('user-message');
if (!userMessageInput) {
  console.error("user-message 요소를 찾을 수 없습니다.");
} else {
  console.log("user-message 로드됨:", userMessageInput);
}

const sendBtn = document.getElementById('send-btn');
const videoBtn = document.getElementById('videoBtn');
const imageBtn = document.getElementById('imageBtn');

// 메시지 전송 함수 (isInitial 플래그를 통해 초기 호출 여부 구분)
async function sendMessage(isInitial = false) {
  let message;
  
  if (isInitial) {
    console.log("초기 메시지 요청 진행");
    // 초기 호출일 경우, 더미 값 "init" 전송 (서버에서 이를 감지하여 초기 인사말을 반환)
    message = "init";
  } else {
    message = userMessageInput.value.trim();
    if (!message) return;
    appendMessage('user', message);
    userMessageInput.value = '';
  }

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // JSON 데이터에 username 필드를 추가합니다.
      body: JSON.stringify({ bot_id: botId, message: message, username: username })
    });
    const data = await response.json();

    // 서버에서는 reply가 문자열이면 그대로, 객체면 {reply, image} 구조로 반환됨.
    let replyText, imagePath;
    if (typeof data.reply === 'object' && data.reply !== null) {
      replyText = data.reply.reply;
      imagePath = data.reply.image ? data.reply.image : null;
    } else {
      replyText = data.reply;
      imagePath = null;
    }
    appendMessage('bot', replyText, imagePath);
  } catch (err) {
    console.error("메시지 전송 에러:", err);
    appendMessage('bot', 'Error: 요청 실패');
  }
}

// 메시지 DOM에 추가 (봇 메시지의 경우, 이미지 있으면 위에 텍스트 출력)
function appendMessage(sender, text, imageSrc) {
  const messageElem = document.createElement('div');
  messageElem.classList.add('message', sender);

  if (sender === 'user') {
    messageElem.textContent = text;
  } else {
    if (imageSrc) {
      const imageContainer = document.createElement('div');
      imageContainer.classList.add('bot-image-container');

      const botImg = document.createElement('img');
      botImg.classList.add('bot-big-img');
      botImg.src = imageSrc;
      botImg.alt = "챗봇 이미지";
      imageContainer.appendChild(botImg);
      messageElem.appendChild(imageContainer);
    }
    const textContainer = document.createElement('div');
    textContainer.classList.add('bot-text-container');
    textContainer.textContent = text;
    messageElem.appendChild(textContainer);
  }

  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  } else {
    console.error("메시지 추가 실패: chatLog가 없음");
  }
}

// 엔터키 또는 전송 버튼으로 메시지 전송
if(userMessageInput){
  userMessageInput.addEventListener('keyup', (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  });
}
if(sendBtn){
  sendBtn.addEventListener('click', () => sendMessage());
}

// 모달 열기/닫기 함수
function openModal(modalId) {
  document.getElementById(modalId).style.display = 'block';
}
function closeModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
}

// 미디어 버튼 이벤트
if(videoBtn){
  videoBtn.addEventListener('click', () => {
    openModal('videoModal');
  });
}
if(imageBtn){
  imageBtn.addEventListener('click', () => {
    openModal('imageModal');
  });
}

// 모달 닫기 버튼 이벤트
document.querySelectorAll('.modal-close').forEach(btn => {
  btn.addEventListener('click', () => {
    const modalId = btn.dataset.closeModal;
    closeModal(modalId);
  });
});

// 페이지 로드 시, 전체 로드가 완료되면 초기 메시지 요청
window.onload = () => {
  console.log("window.onload: 페이지 완전 로드됨");
  // 1초 후 초기 메시지 요청 (페이지에 요소들이 모두 보장된 후)
  setTimeout(() => {
    if (chatLog && chatLog.childElementCount === 0) {
      console.log("초기 메시지 요청: chatLog가 비어 있음");
      sendMessage(true);
    } else {
      console.log("chatLog에 이미 메시지가 있음:", chatLog.childElementCount);
    }
  }, 1000);
};
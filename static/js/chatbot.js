console.log("챗봇 JS 로드 완료");

// DOM 요소
const chatArea = document.querySelector(".chat-area");
const username = chatArea ? chatArea.dataset.username : "사용자";
const chatLog = document.getElementById("chat-log");
const userMessageInput = document.getElementById("user-message");
const sendBtn = document.getElementById("send-btn");
const videoBtn = document.getElementById("videoBtn");
const imageBtn = document.getElementById("imageBtn");

// ============================================
// 임시로 만든 버튼 기능, 나중에 수정 필요
// ============================================

// 버튼 렌더링 함수
function renderButtons(buttons) {
  if (!buttons || buttons.length === 0) return;
  
  const buttonContainer = document.createElement('div');
  buttonContainer.classList.add('button-container');
  buttonContainer.style.cssText = `
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 15px 0;
    padding: 10px;
    justify-content: center;
  `;
  
  buttons.forEach(buttonText => {
    const button = document.createElement('button');
    button.classList.add('choice-button');
    button.textContent = buttonText;
    button.style.cssText = `
      padding: 12px 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.95rem;
      font-weight: 500;
      transition: all 0.3s;
      box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
    `;
    
    button.onmouseover = () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 20px rgba(118, 75, 162, 0.4)';
    };
    
    button.onmouseout = () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 15px rgba(118, 75, 162, 0.3)';
    };
    
    button.onclick = () => {
      userMessageInput.value = buttonText;
      sendMessage();
      buttonContainer.remove();
    };
    
    buttonContainer.appendChild(button);
  });
  
  chatLog.appendChild(buttonContainer);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// 입력창 활성화/비활성화 함수
function setInputEnabled(enabled) {
  if (userMessageInput) {
    userMessageInput.disabled = !enabled;
    userMessageInput.placeholder = enabled 
      ? "메시지를 입력하세요..." 
      : "버튼을 클릭해주세요...";
    userMessageInput.style.opacity = enabled ? '1' : '0.5';
  }
  if (sendBtn) {
    sendBtn.disabled = !enabled;
    sendBtn.style.opacity = enabled ? '1' : '0.5';
    sendBtn.style.cursor = enabled ? 'pointer' : 'not-allowed';
  }
}

// ============================================
// 임시 버튼 기능 끝
// ============================================

// 메시지 전송 함수
async function sendMessage(isInitial = false) {
  let message;

  if (isInitial) {
    message = "init";
  } else {
    message = userMessageInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    userMessageInput.value = "";
  }

  // 로딩 표시
  const loadingId = appendMessage("bot", "생각 중...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        username: username,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // 로딩 메시지 제거
    removeMessage(loadingId);

    // 응답 파싱
    let replyText, imagePath;
    if (typeof data.reply === "object" && data.reply !== null) {
      replyText = data.reply.reply || data.reply;
      imagePath = data.reply.image || null;
    } else {
      replyText = data.reply;
      imagePath = data.image || null;
    }

    appendMessage("bot", replyText, imagePath);
    
    // ============================================
    // 임시로 만든 버튼 처리, 나중에 수정 필요
    // ============================================
    
    // 버튼이 있으면 렌더링하고 입력창 비활성화
    if (data.buttons && data.buttons.length > 0) {
      renderButtons(data.buttons);
      setInputEnabled(false);
    } else {
      setInputEnabled(true);
    }
    
    // ============================================
    // 임시 버튼 처리 끝
    // ============================================
  } catch (err) {
    console.error("메시지 전송 에러:", err);
    removeMessage(loadingId);
    appendMessage("bot", "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.");
  }
}

// 메시지 DOM에 추가
let messageIdCounter = 0;
function appendMessage(sender, text, imageSrc = null) {
  const messageId = `msg-${messageIdCounter++}`;
  const messageElem = document.createElement("div");
  messageElem.classList.add("message", sender);
  messageElem.id = messageId;

  if (sender === "user") {
    messageElem.textContent = text;
  } else {
    // 이미지가 있으면 먼저 표시
    if (imageSrc) {
      const botImg = document.createElement("img");
      botImg.classList.add("bot-big-img");
      botImg.src = imageSrc;
      botImg.alt = "챗봇 이미지";
      messageElem.appendChild(botImg);
    }

    // 텍스트 추가
    const textContainer = document.createElement("div");
    textContainer.classList.add("bot-text-container");
    textContainer.textContent = text;
    messageElem.appendChild(textContainer);
  }

  if (chatLog) {
    chatLog.appendChild(messageElem);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  return messageId;
}

// 메시지 제거
function removeMessage(messageId) {
  const elem = document.getElementById(messageId);
  if (elem) {
    elem.remove();
  }
}

// 엔터키로 전송
if (userMessageInput) {
  userMessageInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  });
}

// 전송 버튼
if (sendBtn) {
  sendBtn.addEventListener("click", () => sendMessage());
}

// 모달 열기/닫기
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "block";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
  }
}

// 미디어 버튼 이벤트
if (videoBtn) {
  videoBtn.addEventListener("click", () => openModal("videoModal"));
}

if (imageBtn) {
  imageBtn.addEventListener("click", () => openModal("imageModal"));
}

// 모달 닫기 버튼
document.querySelectorAll(".modal-close").forEach((btn) => {
  btn.addEventListener("click", () => {
    const modalId = btn.dataset.closeModal;
    closeModal(modalId);
  });
});

// 모달 배경 클릭 시 닫기
document.querySelectorAll(".modal").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });
});

// 페이지 로드 시 초기 메시지 요청
window.addEventListener("load", () => {
  console.log("페이지 로드 완료");
  
  // 임시: 초기에는 입력창 비활성화 (버튼 대기)
  setInputEnabled(false);

  setTimeout(() => {
    if (chatLog && chatLog.childElementCount === 0) {
      console.log("초기 메시지 요청");
      sendMessage(true);
    }
  }, 500);
});

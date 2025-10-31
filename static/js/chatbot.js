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
  buttonContainer.classList.add('quick-reply-buttons');
// buttonContainer.style.cssText 인라인 스타일 제거 (CSS 파일/style 태그로 이동)
  
  // 현재 선택된 사용자 테마를 보관
  function setUserTheme(themeKey) {
    if (!chatLog) return;
    const themeClasses = [
      'user-theme-regret',
      'user-theme-love',
      'user-theme-anxiety',
      'user-theme-dream'
    ];
    // remove from chatLog and body to keep a single active theme
    themeClasses.forEach(c => {
      chatLog.classList.remove(c);
      document.body.classList.remove(c);
    });
    if (themeKey) {
      const cls = `user-theme-${themeKey}`;
      chatLog.classList.add(cls);
      document.body.classList.add(cls);
    }
  }

  buttons.forEach(buttonText => {
    const button = document.createElement('button');
    // 공통 클래스와 개별 클래스 추가
    button.classList.add('reply-btn'); 
    
    // 버튼 텍스트에 따라 개별 클래스 추가
    if (buttonText.includes('후회')) {
        button.classList.add('regret-room');
    } else if (buttonText.includes('사랑')) {
        button.classList.add('love-room');
    } else if (buttonText.includes('불안')) {
        button.classList.add('anxiety-room');
    } else if (buttonText.includes('꿈')) {
        button.classList.add('dream-room');
    } else {
        // 기본 버튼 스타일 (선택 사항)
        button.classList.add('default-room');
    }
    
    button.textContent = buttonText;
    
    // button.style.cssText 인라인 스타일 제거
    // onmouseover, onmouseout 이벤트 제거 (CSS :hover로 대체)
    
    button.onclick = () => {
      // 버튼 종류에 따라 사용자 말풍선 테마 지정
      if (button.classList.contains('regret-room')) setUserTheme('regret');
      if (button.classList.contains('love-room')) setUserTheme('love');
      if (button.classList.contains('anxiety-room')) setUserTheme('anxiety');
      if (button.classList.contains('dream-room')) setUserTheme('dream');
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
  console.log("로딩 메시지 ID:", loadingId);

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
    console.log("응답 데이터:", data);


    // ============================================
    // 임시로 만든 연속 메시지 처리, 나중에 수정 필요
    // ============================================
    
    // 연속 메시지 처리 (replies 배열)
    if (data.replies && Array.isArray(data.replies)) {
      removeMessage(loadingId);
      // 각 메시지를 순차적으로 렌더링
      data.replies.forEach((replyText, index) => {
        const splitMessages = splitLongMessage(replyText, 120); // ✅ 변수명 수정

        splitMessages.forEach((msg, subIndex) => {
          setTimeout(() => {
            // ✅ 첫 메시지 출력 후 로딩 제거
            if (index === 0 && subIndex === 0) removeMessage(loadingId);
            appendMessage("bot", msg, null, false);
            chatLog.scrollTop = chatLog.scrollHeight;
          }, (index * splitMessages.length + subIndex) * 800);
        });

        if (index === data.replies.length - 1) {
          setTimeout(() => {
            if (data.buttons && data.buttons.length > 0) {
              renderButtons(data.buttons);
              setInputEnabled(false);
            } else {
              setInputEnabled(true);
            }
          }, (index + 1) * 1000);
        }
      });
    } else {
      // 기존 단일 메시지 처리
      removeMessage(loadingId);
      let replyText, imagePath;
      if (typeof data.reply === "object" && data.reply !== null) {
        replyText = data.reply.reply || data.reply;
        imagePath = data.reply.image || null;
      } else {
        replyText = data.reply;
        imagePath = data.image || null;
      }

      appendMessage("bot", replyText, imagePath);
      
      // 버튼이 있으면 렌더링하고 입력창 비활성화
      if (data.buttons && data.buttons.length > 0) {
        renderButtons(data.buttons);
        setInputEnabled(false);
      } else {
        setInputEnabled(true);
      }
    }
    
    // ============================================
    // 임시 처리 끝
    // ============================================
  } catch (err) {
    console.error("메시지 전송 에러:", err);
    removeMessage(loadingId);
    appendMessage("bot", "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.");
  }
}

// 메시지 DOM에 추가
// [수정된 appendMessage 함수 전체]
// 메시지 DOM에 추가
let messageIdCounter = 0; // 전역 카운터를 유지 (함수 밖에 있어야 함)

function appendMessage(sender, text, imageSrc = null) {
  const messageId = `msg-${messageIdCounter++}`; // 고유 ID 부여
  const messages = splitLongMessage(text, 120); // ← 메시지를 분할합니다.

  messages.forEach((msg, idx) => {
    const messageElem = document.createElement("div");
    messageElem.classList.add("message", sender);
    // 분할된 메시지에도 고유 ID를 부여합니다.
    messageElem.id = `${messageId}-${idx}`;
    messageElem.style.opacity = "0"; // 초기 투명하게 설정 (fadeIn을 위해)

    if (sender === "user") {
      messageElem.textContent = msg;
    } else {
      // 이미지는 첫 번째 분할 메시지에만 추가
      if (imageSrc && idx === 0) {
        const botImg = document.createElement("img");
        botImg.classList.add("bot-big-img");
        botImg.src = imageSrc;
        botImg.alt = "챗봇 이미지";
        messageElem.appendChild(botImg);
      }

      const textContainer = document.createElement("div");
      textContainer.classList.add("bot-text-container");
      textContainer.textContent = msg;
      messageElem.appendChild(textContainer);
    }

    if (chatLog) {
      chatLog.appendChild(messageElem);
      
      // 각 말풍선 사이 딜레이를 사용하여 순차적으로 표시합니다.
      setTimeout(() => {
        messageElem.style.opacity = "1";
        chatLog.scrollTop = chatLog.scrollHeight;
      }, idx * 500); // 0.5초 간격으로 표시

      // 사용자 말풍선: 한 줄이면 오른쪽 정렬, 여러 줄이면 왼쪽 정렬로 전환
      if (sender === "user") {
        setTimeout(() => {
          const computed = window.getComputedStyle(messageElem);
          const lineHeight = parseFloat(computed.lineHeight);
          const height = messageElem.getBoundingClientRect().height;
          if (lineHeight && height > lineHeight * 1.6) {
            messageElem.classList.add("multi-line");
          }
        }, 0);
      }

    }
  });

  return messageId;
}

function splitLongMessage(text, maxLen = 120) {
  const result = [];
  let current = "";

  const sentences = text.split(/(?<=[.?!…])\s+/); // 문장 단위로 나눔
  sentences.forEach((s) => {
    if ((current + s).length > maxLen) {
      result.push(current.trim());
      current = s + " ";
    } else {
      current += s + " ";
    }
  });
  if (current.trim()) result.push(current.trim());
  return result;
}

// 메시지 제거
function removeMessage(messageId) {
  const elem = document.getElementById(messageId);
  if (elem) {
    elem.remove();
    return;
  }
  // 분할 메시지(ID가 `${messageId}-0` 형태)까지 포함해서 제거
  const candidates = chatLog ? chatLog.querySelectorAll(`[id^="${messageId}-"]`) : [];
  if (candidates && candidates.length > 0) {
    candidates.forEach((el) => el.remove());
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

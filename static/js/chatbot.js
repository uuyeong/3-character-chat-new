console.log("챗봇 JS 로드 완료");

// DOM 요소
const chatArea = document.querySelector(".chat-area");
const username = chatArea ? chatArea.dataset.username : "사용자";
const chatLog = document.getElementById("chat-log");
const userMessageInput = document.getElementById("user-message");
const sendBtn = document.getElementById("send-btn");
const videoBtn = document.getElementById("videoBtn");
const imageBtn = document.getElementById("imageBtn");

const BOT_AVATAR_SRC = "/static/images/hateslop/owl1.png";

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
      // 방 버튼 확인 및 입장 메시지 표시
      let roomName = null;
      let roomImage = null;
      
      if (button.classList.contains('regret-room')) {
        setUserTheme('regret');
        roomName = '후회의 방';
        roomImage = '/static/images/chatbot/regret_room.png';

      } else if (button.classList.contains('love-room')) {
        setUserTheme('love');
        roomName = '사랑의 방';
        roomImage = '/static/images/chatbot/love_room.png';
      } else if (button.classList.contains('anxiety-room')) {
        setUserTheme('anxiety');
        roomName = '불안의 방';
        roomImage = '/static/images/chatbot/anxiety_room.png';
      } else if (button.classList.contains('dream-room')) {
        setUserTheme('dream');
        roomName = '꿈의 방';
        roomImage = '/static/images/chatbot/dream_room.png';
      }

      // 방 입장 메시지 표시 (방 버튼일 경우만)
      if (roomName && roomImage) {
        showRoomEntrance(roomName, roomImage);
      }
      
      userMessageInput.value = buttonText;
      sendMessage();
      buttonContainer.remove();
    };

    buttonContainer.appendChild(button);
  });

  chatLog.appendChild(buttonContainer);
  scrollToBottomSmooth();
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

// 방 입장 메시지 표시
function showRoomEntrance(roomName, roomImageSrc) {
  if (!chatLog) return;

  const container = document.createElement("div");
  container.classList.add("room-entrance-message");
  container.style.cssText = `
    text-align: center;
    opacity: 0;
    transition: opacity 0.8s ease-in;
    margin: 30px 0;
  `;

  // 방 이미지
  const img = document.createElement("img");
  img.src = roomImageSrc;
  img.alt = `${roomName} 이미지`;
  img.style.cssText = `
    width: 90%;
    max-width: 500px;
    height: auto;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-bottom: 16px;
  `;

  // 텍스트
  const text = document.createElement("div");
  text.style.cssText = `
    font-size: 1.1rem;
    color: #555;
    font-weight: 600;
    margin-top: 12px;
  `;
  text.textContent = `${roomName}에 입장했습니다.`;

  // DOM 연결
  container.appendChild(img);
  container.appendChild(text);
  chatLog.appendChild(container);

  // 부드럽게 나타나는 효과
  setTimeout(() => {
    container.style.opacity = "1";
  }, 100);

  scrollToBottomSmooth();
}

function showEnvelopePreview(letterText, buttons = [], stampImageSrc = null) {
  const previewContainer = document.createElement("div");
  previewContainer.classList.add("letter-preview-container");
  previewContainer.style.cssText = `
    text-align: center;
    padding: 20px;
    margin: 20px auto;
    max-width: 600px;
  `;

  // 봉투 + 우표를 담을 컨테이너 (position: relative)
  const envelopeWrapper = document.createElement("div");
  envelopeWrapper.style.cssText = `
    position: relative;
    display: inline-block;
    width: 95%;
    margin: 20px auto;
  `;

  // 편지 봉투 이미지
  const envelopeImg = document.createElement("img");
  envelopeImg.src = "/static/images/chatbot/a_full_envelope.png";
  envelopeImg.alt = "편지 봉투";
  envelopeImg.style.cssText = `
    width: 110%;
    display: block;
  `;

  // 우표 이미지 (오른쪽 상단에 겹치기)
  if (stampImageSrc) {
    const stampImg = document.createElement("img");
    stampImg.src = stampImageSrc;
    stampImg.alt = "우표";
    stampImg.classList.add("envelope-stamp");
    stampImg.style.cssText = `
      position: absolute;
      top: 15%;
      right: 11%;
      width: 13%;
      height: auto;
      z-index: 10;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      border-radius: 4px;
    `;
    envelopeWrapper.appendChild(stampImg);
  }

  envelopeWrapper.appendChild(envelopeImg);

  // 안내 메시지
  const messageDiv = document.createElement("p");
  messageDiv.textContent = "편지를 열어보겠나?";
  messageDiv.style.cssText = `
    margin: 15px 0;
    font-size: 1.1em;
  `;

  // 버튼 컨테이너
  const btnContainer = document.createElement("div");
  btnContainer.style.marginTop = "20px";

  // 예/아니오 버튼
  const yesBtn = document.createElement("button");
  yesBtn.textContent = "예";
  yesBtn.classList.add("reply-btn");
  yesBtn.onclick = () => {
    previewContainer.remove();
    showLetter(letterText, buttons, stampImageSrc);
  };

  const noBtn = document.createElement("button");
  noBtn.textContent = "아니오";
  noBtn.classList.add("reply-btn");
  noBtn.onclick = () => {
    previewContainer.remove();
    appendMessage("bot", "알았어. 편지를 열고 싶을때 말해줘");
    scrollToBottomSmooth();
    setInputEnabled(true);
  };

  btnContainer.appendChild(yesBtn);
  btnContainer.appendChild(noBtn);

  previewContainer.appendChild(envelopeWrapper);  // envelopeImg 대신 envelopeWrapper 추가
  previewContainer.appendChild(messageDiv);
  previewContainer.appendChild(btnContainer);

  chatLog.appendChild(previewContainer);
  scrollToBottomSmooth();
}

function backToChatEntrance() {
  const letterContainer = document.getElementById("letterContainer");
  const chatLog = document.getElementById("chat-log");

  if (letterContainer) letterContainer.style.display = "none";
  if (chatLog) chatLog.style.display = "block";

  renderButtons(["별빛 우체국에 다시 한번 입장"]);

  setInputEnabled(true);
  scrollToBottomSmooth();
}

// showLetter 함수
function showLetter(letterText, buttons = [], stampImageSrc = null) {
  console.log("[showLetter] 시작 - 텍스트 길이:", letterText ? letterText.length : 0, "버튼 개수:", buttons ? buttons.length : 0, "우표:", stampImageSrc);
  
  const letterContainer = document.getElementById("letterContainer");
  const letterTextDiv = document.getElementById("letterText");
  const letterButtonsDiv = document.getElementById("letterButtons");
  
  if (!letterContainer || !letterTextDiv) {
    console.error("[showLetter] letterContainer 또는 letterText를 찾을 수 없습니다!");
    return;
  }
  
  // 편지 텍스트 표시
  letterTextDiv.textContent = letterText;
  console.log("[showLetter] 편지 텍스트 설정 완료");

  // 우표 이미지 추가 (오른쪽 상단)
  let stampImg = document.getElementById("letterStamp");
  if (stampImageSrc) {
    if (!stampImg) {
      stampImg = document.createElement("img");
      stampImg.id = "letterStamp";
      stampImg.classList.add("letter-stamp");
      letterContainer.appendChild(stampImg);
    }
    stampImg.src = stampImageSrc;
    stampImg.style.display = "block";
  } else {
    if (stampImg) stampImg.style.display = "none";
  }

  // 버튼 표시
  if (letterButtonsDiv) {
    letterButtonsDiv.innerHTML = ""; // 기존 버튼 제거

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "편지 닫기";
    closeBtn.classList.add("reply-btn", "dream-room"); // 색상 클래스는 취향대로

    closeBtn.style.margin = "0 auto";
    closeBtn.style.padding = "12px 24px";
    closeBtn.style.borderRadius = "25px";

    closeBtn.onclick = () => {
      backToChatEntrance();
    };

    letterButtonsDiv.appendChild(closeBtn);

  }

  // 챗 영역 숨기고 편지 표시
  letterContainer.style.display = "block";
  chatLog.style.display = "none";

  // 스크롤 맨 위로
  window.scrollTo({ top: 0, behavior: "smooth" });
  
  console.log("[showLetter] 편지 표시 완료:", letterText.substring(0, 50) + "...");
}


// ============================================
// 임시 버튼 기능 끝
// ============================================

// 메시지 전송 함수
function showEntranceMessage() {
  if (!chatLog) return;

  const container = document.createElement("div");
  container.classList.add("entrance-message");

  // 이미지
  const img = document.createElement("img");
  img.src = "/static/images/chatbot/main_background2.png"; 
  img.alt = "별빛 우체국 로고";
  img.classList.add("entrance-img");

  // 텍스트
  const text = document.createElement("div");
  text.classList.add("entrance-text");
  text.textContent = `${username}님이 별빛 우체국에 입장했습니다.`;

  // DOM 연결
  container.appendChild(img);
  container.appendChild(text);
  chatLog.appendChild(container);

  // 부드럽게 나타나는 효과
  setTimeout(() => {
    container.style.opacity = "1";
  }, 100);

  scrollToBottomSmooth();
}

async function sendMessage(isInitial = false) {
  let message = isInitial ? "init" : userMessageInput.value.trim();
  if (!isInitial) {
    if (!message) return;
    appendMessage("user", message);
    userMessageInput.value = "";
  }

  const loadingId = appendMessage("bot", "생각 중...", null, { showAvatar: false });

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, username }),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const data = await response.json();
    removeMessage(loadingId);
    console.log("응답 데이터:", data);
    // 봉투 편지 메시지
    if (data.is_letter_end && data.letter) {
      // ✅ stamp_description이 있으면 우선 사용, 없으면 extractStampOnly로 추출
      const stampDescription = data.stamp_description;
      const stampReplies = stampDescription 
        ? [stampDescription] 
        : extractStampOnly(Array.isArray(data.replies) ? data.replies : []);
      
      if (stampReplies.length) {
        // 우표 설명 말풍선 먼저
        stampReplies.forEach((replyText, index) => {
          setTimeout(() => {
            const showAvatar = index === 0;
            appendMessage("bot", replyText, null, { showAvatar });
            scrollToBottomSmooth();
          }, index * 800);
        });
        // 그 다음 봉투 미리보기
        setTimeout(() => {
          const stampSrc = data.stamp_image || (data.stamp_code ? `/static/images/chatbot/${data.stamp_code}.png` : null);
          showEnvelopePreview(data.letter, data.buttons || [], stampSrc);
        }, stampReplies.length * 800 + 300);
      } else {
        // 설명이 없으면 즉시 봉투
        const stampSrc = data.stamp_image || (data.stamp_code ? `/static/images/chatbot/${data.stamp_code}.png` : null);
        showEnvelopePreview(data.letter, data.buttons || [], stampSrc);
      }
      return; 
    }

    // 일반 연속 메시지
    if (Array.isArray(data.replies)) {
      data.replies.forEach((replyText, index) => {
        const splitMessages = splitLongMessage(replyText, 120);
        splitMessages.forEach((msg, subIndex) => {
          setTimeout(() => {
            const showAvatar = index === 0 && subIndex === 0;
            appendMessage("bot", msg, null, { showAvatar });
            scrollToBottomSmooth();
          }, (index * splitMessages.length + subIndex) * 800);
        });
        if (index === data.replies.length - 1) {
          setTimeout(() => {
            if (data.buttons?.length) {
              renderButtons(data.buttons);
              setInputEnabled(false);
            } else setInputEnabled(true);
          }, (index + 1) * 1000);
        }
      });
      return;
    }

    // 기존 단일 메시지
    let replyText, imagePath;
    if (typeof data.reply === "object" && data.reply !== null) {
      replyText = data.reply.reply || data.reply;
      imagePath = data.reply.image || null;
    } else {
      replyText = data.reply;
      imagePath = data.image || null;
    }

    appendMessage("bot", replyText, imagePath);
    if (data.buttons?.length) {
      renderButtons(data.buttons);
      setInputEnabled(false);
    } else setInputEnabled(true);

  } catch (err) {
    console.error("메시지 전송 에러:", err);
    removeMessage(loadingId);
    appendMessage("bot", "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.");
  }
}

function extractStampOnly(replies = []) {
  return replies.filter(t => t && t.length <= 140 && !/^to[\s.:]/i.test(t.trim()));
}
function scrollToBottomSmooth() {
  if (!chatLog) return;
  requestAnimationFrame(() => {
    setTimeout(() => {
      chatLog.scrollTo({
        top: chatLog.scrollHeight,
        behavior: "smooth"
      });
    }, 80);
  });
}
/*function showStamp(stampCode) {
  const stampImg = document.getElementById("stampImage");
  stampImg.src = `/static/images/chatbot/${stampCode}.png`; 
  stampImg.style.display = "block";
}*/

let messageIdCounter = 0;

function appendMessage(sender, text, imageSrc = null, options = {}) {
  const { showAvatar = sender === "bot", avatarSrc = BOT_AVATAR_SRC } = options;
  const messageId = `msg-${messageIdCounter++}`;
  const messages = splitLongMessage(text, 120);

  if (!chatLog) {
    return messageId;
  }

  if (sender === "bot") {
    const groupElem = document.createElement("div");
    groupElem.classList.add("message-group", "bot-group");
    groupElem.id = messageId;

    if (showAvatar) {
      const avatarContainer = document.createElement("div");
      avatarContainer.classList.add("bot-avatar");
      const avatarImg = document.createElement("img");
      avatarImg.src = avatarSrc;
      avatarImg.alt = "부엉장 프로필";
      avatarContainer.appendChild(avatarImg);
      groupElem.appendChild(avatarContainer);
    } else {
      groupElem.classList.add("bot-group-no-avatar");
    }

    const bubbleContainer = document.createElement("div");
    bubbleContainer.classList.add("bot-bubble-container");
    groupElem.appendChild(bubbleContainer);

    if (imageSrc) {
      const botImg = document.createElement("img");
      botImg.classList.add("bot-big-img");
      botImg.src = imageSrc;
      botImg.alt = "챗봇 이미지";
      bubbleContainer.appendChild(botImg);
    }

    messages.forEach((msg, idx) => {
      if (!msg) return;
      const messageElem = document.createElement("div");
      messageElem.classList.add("message", "bot");
      messageElem.id = `${messageId}-${idx}`;
      messageElem.style.opacity = "0";
      messageElem.textContent = msg;
      bubbleContainer.appendChild(messageElem);

      setTimeout(() => {
        messageElem.style.opacity = "1";
        scrollToBottomSmooth();
      }, idx * 500);
    });

    chatLog.appendChild(groupElem);
    return messageId;
  }

  messages.forEach((msg, idx) => {
    if (!msg) return;
    const messageElem = document.createElement("div");
    messageElem.classList.add("message", sender);
    messageElem.id = `${messageId}-${idx}`;
    messageElem.style.opacity = "0";
    messageElem.textContent = msg;
    chatLog.appendChild(messageElem);

    setTimeout(() => {
      messageElem.style.opacity = "1";
      scrollToBottomSmooth();

      if (sender === "user") {
        const computed = window.getComputedStyle(messageElem);
        const lineHeight = parseFloat(computed.lineHeight);
        const height = messageElem.getBoundingClientRect().height;
        if (lineHeight && height > lineHeight * 1.6) {
          messageElem.classList.add("multi-line");
        }
      }
    }, idx * 500);
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
  showEntranceMessage();
  setInputEnabled(false);

  setTimeout(() => {
      console.log("초기 메시지 요청");
      sendMessage(true);
    }, 1500);
});
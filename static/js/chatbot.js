console.log("챗봇 JS 로드 완료");

// DOM 요소
const chatArea = document.querySelector(".chat-area");
const username = chatArea ? chatArea.dataset.username : "사용자";
const chatLog = document.getElementById("chat-log");
const userMessageInput = document.getElementById("user-message");
const sendBtn = document.getElementById("send-btn");
const videoBtn = document.getElementById("videoBtn");
const imageBtn = document.getElementById("imageBtn");

const BOT_AVATAR_SRC = "/static/images/chatbot/owl/owl_profile.png";

// 우표 이름 매핑 (2단어 이름)
const STAMP_NAMES = {
  'R_1': '미련 별',
  'R_2': '침묵 끝',
  'R_3': '단절 선',
  'R_4': '공전 멈춤',
  'L_1': '스침 빛',
  'L_2': '봉오리 마음',
  'L_3': '정지 시간',
  'L_4': '균열 복원',
  'L_5': '엇갈림 실',
  'L_6': '반복 틈',
  'D_1': '흐릿 길',
  'D_2': '현실 벽',
  'D_3': '두려움 극복',
  'D_4': '공허 정상',
  'D_5': '내면 빛',
  'A_1': '연결 끈',
  'A_2': '갈림 판단',
  'A_3': '성과 짐',
  'A_4': '존재 탐구'
};

// 마지막 편지 정보 저장 (편지 다시 보기용)
let lastLetterInfo = {
  text: null,
  buttons: [],
  stampImageSrc: null
};

// 감정에 따른 아바타 이미지 매핑
const EMOTION_AVATAR_MAP = {
  "슬픔": "/static/images/chatbot/owl/sad_owl.png",
  "기쁨": "/static/images/chatbot/owl/happy_owl.png",
  "분노": "/static/images/chatbot/owl/angry_owl.png",
  "의문": "/static/images/chatbot/owl/question_owl.png",
  "기본": BOT_AVATAR_SRC
};

// 감정 태그 파싱 함수
function parseEmotionTag(text) {
  const emotionRegex = /##감정\s*:\s*([^\n]+)/;
  const match = text.match(emotionRegex);
  if (match) {
    const emotion = match[1].trim();
    // 감정 태그 제거
    const cleanText = text.replace(emotionRegex, "").trim();
    return { emotion, cleanText };
  }
  return { emotion: null, cleanText: text };
}

function formatStampText(text) {

  const stampNameRegex = /(이 우표의 이름은\s+)([^.]+?)(이다\.)/;
  const match = text.match(stampNameRegex);
  
  if (match) {
    const before = match[1]; 
    const content = match[2].trim(); 
    const after = match[3];   

    return text.replace(stampNameRegex, `${before}<strong>${content}</strong>${after}`);
  }

  const stampRegex = /(이건\s+)(.+?)(\s+우표야)/;
  const oldMatch = text.match(stampRegex);
  
  if (oldMatch) {
    const before = oldMatch[1]; 
    const content = oldMatch[2];
    const after = oldMatch[3];  
    
    // 중간 부분 전체를 <strong> 태그로 감싸기
    return text.replace(stampRegex, `${before}<strong>${content}</strong>${after}`);
  }
  
  // 패턴이 없으면 원본 반환
  return text;
}

// 감정에 따른 아바타 이미지 가져오기
function getAvatarForEmotion(emotion) {
  if (!emotion) return BOT_AVATAR_SRC;
  return EMOTION_AVATAR_MAP[emotion] || BOT_AVATAR_SRC;
}

// 우표 확대 모달 표시
function showStampModal(stampImageSrc) {
  // 기존 모달이 있으면 제거
  const existingModal = document.getElementById('stampModal');
  if (existingModal) {
    existingModal.remove();
  }

  // 모달 컨테이너 생성
  const modal = document.createElement('div');
  modal.id = 'stampModal';

  // 모달 내용 컨테이너
  const modalContent = document.createElement('div');
  modalContent.classList.add('modal-content');

  // 닫기 버튼
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '&times;';
  closeBtn.classList.add('modal-close-btn');

  // 우표 이미지
  const stampImg = document.createElement('img');
  stampImg.src = stampImageSrc;
  stampImg.alt = '우표 확대';
  stampImg.classList.add('stamp-img');

  // 닫기 함수
  const closeModal = () => {
    modal.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => {
      modal.remove();
    }, 300);
  };

  // 이벤트 리스너
  closeBtn.onclick = closeModal;
  modal.onclick = (e) => {
    if (e.target === modal) {
      closeModal();
    }
  };

  // ESC 키로 닫기
  const handleEsc = (e) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', handleEsc);
    }
  };
  document.addEventListener('keydown', handleEsc);

  // 요소 조립
  modalContent.appendChild(closeBtn);
  modalContent.appendChild(stampImg);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
}

// 테마 설정 함수
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
    // 재입장 시 설정한 인라인 스타일 제거 (테마 배경이 적용되도록)
    chatLog.style.backgroundColor = '';
    chatLog.style.backgroundImage = '';
  } else {
    // 테마가 없을 때는 흰색 배경 유지
    chatLog.style.backgroundColor = '#FFFFFF';
    chatLog.style.backgroundImage = 'none';
  }
}

// 버튼 렌더링 함수
function renderButtons(buttons) {
  if (!buttons || buttons.length === 0) return;
  
  const buttonContainer = document.createElement('div');
  buttonContainer.classList.add('quick-reply-buttons');
// buttonContainer.style.cssText 인라인 스타일 제거 (CSS 파일/style 태그로 이동)

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
  
    
    button.onclick = () => {
      // "편지 다시 보기" 버튼 처리
      if (buttonText === "편지 다시 보기") {
        if (lastLetterInfo.text) {
          showLetter(lastLetterInfo.text, lastLetterInfo.buttons, lastLetterInfo.stampImageSrc);
          buttonContainer.remove();
        }
        return;
      }
      
      // 재입장 관련 버튼 처리 (다양한 버튼 텍스트 지원)
      if (buttonText.includes("재입장") || buttonText.includes("다시 입장") || buttonText === "별빛 우체국에 다시 한번 입장") {
        buttonContainer.remove();
        reEnterPostOffice();
        return;
      }
      
      // 방 버튼 확인 및 입장 메시지 표시
      let roomName = null;
      let roomImage = null;
      
      if (button.classList.contains('regret-room')) {
        setUserTheme('regret');
        roomName = '후회의 방';
        roomImage = '/static/images/chatbot/room/regret_room.png';

      } else if (button.classList.contains('love-room')) {
        setUserTheme('love');
        roomName = '사랑의 방';
        roomImage = '/static/images/chatbot/room/love_room.png';
      } else if (button.classList.contains('anxiety-room')) {
        setUserTheme('anxiety');
        roomName = '불안의 방';
        roomImage = '/static/images/chatbot/room/anxiety_room.png';
      } else if (button.classList.contains('dream-room')) {
        setUserTheme('dream');
        roomName = '꿈의 방';
        roomImage = '/static/images/chatbot/room/dream_room.png';
      }

      // 방 입장 메시지 표시
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
  container.classList.add("entrance-message");

  // 방 이미지
  const img = document.createElement("img");
  img.src = roomImageSrc;
  img.alt = `${roomName} 이미지`;
  img.classList.add("entrance-img");

  // 텍스트
  const text = document.createElement("div");
  text.classList.add("entrance-text");
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
    max-width: 100%;
    box-sizing: border-box;
  `;

  // 봉투 + 우표를 담을 컨테이너 (position: relative)
  const envelopeWrapper = document.createElement("div");
  envelopeWrapper.style.cssText = `
    position: relative;
    display: inline-block;
    width: 100%;
    max-width: 500px;
    margin: 20px auto;
    overflow: hidden;
    border-radius: 12px;
    box-sizing: border-box;
  `;

  // 편지 봉투 이미지
  const envelopeImg = document.createElement("img");
  envelopeImg.src = "/static/images/chatbot/letter/a_full_envelope.png";
  envelopeImg.alt = "편지 봉투";
  envelopeImg.style.cssText = `
    width: 100%;
    height: 100%;
    display: block;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    object-fit: cover;
    object-position: 48% center;
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
      transform: rotate(2deg);
      transition: all 0.3s ease;
      cursor: pointer;
      animation: stampFloat 3s ease-in-out infinite;
    `;
    
    // 우표 애니메이션 키프레임 추가
    if (!document.getElementById('stamp-animation-style')) {
      const style = document.createElement('style');
      style.id = 'stamp-animation-style';
      style.textContent = `
        @keyframes stampFloat {
          0%, 100% {
            transform: rotate(2deg) translateY(0px);
          }
          50% {
            transform: rotate(2deg) translateY(-5px);
          }
        }
      `;
      document.head.appendChild(style);
    }
    
    // 호버 효과
    stampImg.addEventListener('mouseenter', () => {
      stampImg.style.transform = 'rotate(0deg) scale(1.15)';
      stampImg.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.3)';
    });
    
    stampImg.addEventListener('mouseleave', () => {
      stampImg.style.transform = 'rotate(2deg) scale(1)';
      stampImg.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';
    });
    
    // 우표 클릭 시 확대 모달 표시
    stampImg.addEventListener('click', () => {
      showStampModal(stampImageSrc);
    });
    
    envelopeWrapper.appendChild(stampImg);
  }

  envelopeWrapper.appendChild(envelopeImg);

  // 안내 메시지
  const messageDiv = document.createElement("p");
  messageDiv.textContent = "지금 편지를 열어보겠나?";
  messageDiv.style.cssText = `
    margin: 15px auto;
    font-size: 1.1rem;
    background: rgba(255, 255, 255, 0.75);
    border-radius: 17px;
    padding: 8px 12px;
    color: #1a1919;
    font-weight: 500;
    display: block;
    width: fit-content;
    text-align: center;
  `;

  // 버튼 컨테이너
  const btnContainer = document.createElement("div");
  btnContainer.style.cssText = `
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 10px;
  `;

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

  // 편지 정보가 있으면 "편지 다시 보기" 버튼도 추가
  const buttons = ["별빛 우체국에 다시 한번 입장"];
  if (lastLetterInfo.text) {
    buttons.push("편지 다시 보기");
  }
  renderButtons(buttons);

  setInputEnabled(true);
  scrollToBottomSmooth();
}

// showLetter 함수
function showLetter(letterText, buttons = [], stampImageSrc = null) {
  console.log("[showLetter] 시작 - 텍스트 길이:", letterText ? letterText.length : 0, "버튼 개수:", buttons ? buttons.length : 0, "우표:", stampImageSrc);
  
  // 편지 정보 저장 (다시 보기용)
  lastLetterInfo = {
    text: letterText,
    buttons: buttons,
    stampImageSrc: stampImageSrc
  };
  
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
      stampImg.style.cursor = "pointer";
      letterContainer.appendChild(stampImg);
    }
    stampImg.src = stampImageSrc;
    stampImg.style.display = "block";
    stampImg.style.cursor = "pointer";
    
    // 기존 클릭 이벤트 제거 후 새로 추가 (중복 방지)
    const newStampImg = stampImg.cloneNode(true);
    stampImg.parentNode.replaceChild(newStampImg, stampImg);
    stampImg = newStampImg;
    
    // 우표 클릭 시 확대 모달 표시
    stampImg.addEventListener('click', () => {
      showStampModal(stampImageSrc);
    });
  } else {
    if (stampImg) stampImg.style.display = "none";
  }

  // 버튼 표시
  if (letterButtonsDiv) {
    letterButtonsDiv.innerHTML = ""; // 기존 버튼 제거

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "편지 닫기";
    closeBtn.classList.add("reply-btn"); // 현재 테마 색상이 자동으로 적용됨

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


// 우체국 재입장 함수
function reEnterPostOffice() {
  // 1. 테마 제거
  setUserTheme(null);
  
  // 2. body 배경색 설정
  if (document.body) {
    document.body.style.backgroundColor = '#f7f7f7';
  }
  
  // 3. 재입장 이미지와 메시지를 먼저 표시
  setTimeout(() => {
    showReEntranceMessage();
    
    // 4. 그 다음 "다시 입구로 가자." 메시지 표시
    setTimeout(() => {
      appendMessage("bot", "다시 입구로 가자.");
      
      // 5. 초기 메시지 전송
      setTimeout(() => {
        sendMessage(true);
      }, 1000);
    }, 1000);
  }, 300);
}

// 재입장 메시지 표시
function showReEntranceMessage() {
  if (!chatLog) return;

  // config의 ui_settings 사용
  const reEntranceSettings = window.UI_SETTINGS?.re_entrance || {};
  const imageSrc = reEntranceSettings.image ? `/static/${reEntranceSettings.image}` : "/static/images/chatbot/background/main_background2.png";
  
  // 메시지에 사용자 이름이 포함되어 있지 않으면 추가
  let message = reEntranceSettings.message || `${username}님이 우체국에 재입장하였습니다.`;
  // Flask 템플릿 변수가 제대로 치환되지 않은 경우를 대비해 동적으로 처리
  if (message.includes('{{ username }}')) {
    message = message.replace('{{ username }}', username);
  }
  // 사용자 이름이 없는 경우 추가
  if (!message.includes(username)) {
    message = `${username}님이 우체국에 재입장하였습니다.`;
  }

  const container = document.createElement("div");
  container.classList.add("entrance-message");

  // 이미지
  const img = document.createElement("img");
  img.src = imageSrc; 
  img.alt = "별빛 우체국 재입장";
  img.classList.add("entrance-img");

  // 텍스트
  const text = document.createElement("div");
  text.classList.add("entrance-text");
  text.textContent = message;

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

// 메시지 전송 함수
function showEntranceMessage() {
  if (!chatLog) return;

  const container = document.createElement("div");
  container.classList.add("entrance-message");

  // 이미지
  const img = document.createElement("img");
  img.src = "/static/images/chatbot/background/main_background2.png"; 
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
      let totalDelay = 0;
      
      // 1단계: 앞의 일반 대화 메시지들 먼저 표시 (편지 발견 메시지 등)
      if (Array.isArray(data.replies) && data.replies.length > 0) {
        const allSplitMessages = [];
        
        // 우표 설명과 편지 내용을 제외한 일반 메시지만 먼저 처리
        const regularReplies = data.replies.filter(text => 
          !text.includes('우표') && 
          !text.includes('stamp') &&
          !text.startsWith('To.') &&  
          !text.startsWith('to.') &&  
          !text.includes('년 전의') && 
          !text.includes('년 후의')    
        );
        
        // 메시지 분할 및 총 시간 계산
        regularReplies.forEach((replyText, index) => {
          const splitMessages = splitLongMessage(replyText, 100);
          allSplitMessages.push({ messages: splitMessages, originalIndex: index });
          totalDelay += splitMessages.length * 800;
        });
        
        // 순차적으로 표시
        let currentDelay = 0;
        allSplitMessages.forEach((item, index) => {
          item.messages.forEach((msg, subIndex) => {
            setTimeout(() => {
              const showAvatar = index === 0 && subIndex === 0;
              appendMessage("bot", msg, null, { showAvatar });
              scrollToBottomSmooth();
            }, currentDelay);
            currentDelay += 800;
          });
        });
      }
      
      // 2단계: 앞의 메시지가 모두 끝난 후 우표 설명 표시
      const stampDescription = data.stamp_description;
      const stampCode = data.stamp_code;
      
      // 우표 설명 메시지에 새 이름 적용
      let processedStampDescription = stampDescription;
      if (stampDescription && stampCode && STAMP_NAMES[stampCode]) {
        const stampName = STAMP_NAMES[stampCode];
        
        processedStampDescription = processedStampDescription.replace(
          /^이건 [^.]* 우표(?:야|지)\.\s*/,
          ''
        );
        
        processedStampDescription = processedStampDescription.replace(
          /자 너의 편지에 붙어 있었던 우표다\./,
          `이 우표의 이름은 ${stampName}이다.`
        );
        processedStampDescription = processedStampDescription.replace(
          /좋아\. 다시 한번 보여주지\. 자 너의 편지에 붙어 있었던 우표다\./,
          `좋아. 다시 한번 보여주지. 이 우표의 이름은 ${stampName}이다.`
        );
      }
      
      const stampReplies = processedStampDescription 
        ? [processedStampDescription] 
        : extractStampOnly(Array.isArray(data.replies) ? data.replies : []);
      
      if (stampReplies.length) {
        // 앞의 메시지 완료 후 1초 대기 후 우표 설명 시작
        const stampStartDelay = totalDelay + 1000;
        
        // 우표 설명을 문장 단위로 분할하여 순차 표시
        const stampSentences = stampReplies[0].split(/(?<=[.?!])\s+/);
        
        stampSentences.forEach((sentence, index) => {
          setTimeout(() => {
            const showAvatar = totalDelay === 0 && index === 0; // 앞에 메시지가 없었으면 첫 우표 메시지에 아바타
            appendMessage("bot", sentence.trim(), null, { showAvatar });
            scrollToBottomSmooth();
          }, stampStartDelay + index * 800);
        });
        
        // 3단계: 우표 설명 완료 후 봉투 미리보기
        setTimeout(() => {
          const stampSrc = data.stamp_image || (data.stamp_code ? `/static/images/chatbot/stamp/${data.stamp_code}.png` : null);
          showEnvelopePreview(data.letter, data.buttons || [], stampSrc);
        }, stampStartDelay + stampSentences.length * 800 + 500);
      } else {
        // 우표 설명이 없으면 앞의 메시지 후 바로 봉투
        setTimeout(() => {
          const stampSrc = data.stamp_image || (data.stamp_code ? `/static/images/chatbot/stamp/${data.stamp_code}.png` : null);
          showEnvelopePreview(data.letter, data.buttons || [], stampSrc);
        }, totalDelay + 500);
      }
      return; 
    }

    // 일반 연속 메시지
    if (Array.isArray(data.replies)) {
      let totalDelay = 0;
      const allSplitMessages = [];
      
      // 모든 메시지를 미리 분할하고 총 지연 시간 계산
      data.replies.forEach((replyText, index) => {
        const splitMessages = splitLongMessage(replyText, 100);
        allSplitMessages.push({ messages: splitMessages, originalIndex: index });
        totalDelay += splitMessages.length * 800;
      });
      
      // 메시지 순차적으로 표시
      let currentDelay = 0;
      allSplitMessages.forEach((item, index) => {
        item.messages.forEach((msg, subIndex) => {
          setTimeout(() => {
            const showAvatar = index === 0 && subIndex === 0;
            appendMessage("bot", msg, null, { showAvatar });
            scrollToBottomSmooth();
          }, currentDelay);
          currentDelay += 800;
        });
      });
      
      // 재입장 관련 키워드 확인
      const isReentranceMessage = message && (
        message.includes("재입장") || 
        message.includes("다시 입장") ||
        message.includes("우체국에 재입장")
      );
      const isReentranceInReplies = data.replies?.some(reply => 
        reply && (reply.includes("재입장") || reply.includes("다시 입장"))
      );
      const hasReentranceButton = data.buttons?.some(btn => 
        btn.includes("재입장") || btn.includes("다시 입장")
      );
      
      // 모든 메시지가 끝난 후 이미지 표시
      setTimeout(() => {
        if (data.image) {
          setTimeout(() => {
            appendMessage("bot", "", data.image, { showAvatar: false });
            scrollToBottomSmooth();
            
            // 이미지 후 추가 메시지가 있으면 표시
            if (Array.isArray(data.replies_after_image) && data.replies_after_image.length > 0) {
              let afterImageDelay = 500; // 이미지 후 대기 시간
              
              data.replies_after_image.forEach((replyText, index) => {
                const splitMessages = splitLongMessage(replyText, 100);
                splitMessages.forEach((msg, subIndex) => {
                  setTimeout(() => {
                    appendMessage("bot", msg, null, { showAvatar: false });
                    scrollToBottomSmooth();
                  }, afterImageDelay);
                  afterImageDelay += 800;
                });
              });
              
              // 이미지 후 메시지까지 모두 끝난 후 버튼 표시 또는 재입장 처리
              setTimeout(() => {
                if ((isReentranceMessage && (isReentranceInReplies || hasReentranceButton)) || hasReentranceButton) {
                  if (hasReentranceButton) {
                    renderButtons(data.buttons);
                    setInputEnabled(false);
                  } else {
                    reEnterPostOffice();
                  }
                } else {
                  if (data.buttons?.length) {
                    renderButtons(data.buttons);
                    setInputEnabled(false);
                  } else {
                    setInputEnabled(true);
                  }
                }
              }, afterImageDelay);
            } else {
              // 이미지 후 메시지가 없으면 바로 버튼 표시 또는 재입장 처리
              if ((isReentranceMessage && (isReentranceInReplies || hasReentranceButton)) || hasReentranceButton) {
                if (hasReentranceButton) {
                  setTimeout(() => {
                    renderButtons(data.buttons);
                    setInputEnabled(false);
                  }, 500);
                } else {
                  setTimeout(() => {
                    reEnterPostOffice();
                  }, 500);
                }
              } else {
                if (data.buttons?.length) {
                  setTimeout(() => {
                    renderButtons(data.buttons);
                    setInputEnabled(false);
                  }, 500);
                } else {
                  setInputEnabled(true);
                }
              }
            }
          }, 300);
        } else {
          if ((isReentranceMessage && (isReentranceInReplies || hasReentranceButton)) || hasReentranceButton) {
            if (hasReentranceButton) {
              setTimeout(() => {
                renderButtons(data.buttons);
                setInputEnabled(false);
              }, 200);
            } else {
              setTimeout(() => {
                reEnterPostOffice();
              }, 200);
            }
          } else {
            if (data.buttons?.length) {
              setTimeout(() => {
                renderButtons(data.buttons);
                setInputEnabled(false);
              }, 200);
            } else {
              setInputEnabled(true);
            }
          }
        }
      }, totalDelay);
      
      return;
    }

    let replyText, imagePath;
    if (typeof data.reply === "object" && data.reply !== null) {
      replyText = data.reply.reply || data.reply;
      imagePath = data.reply.image || null;
    } else {
      replyText = data.reply;
      imagePath = data.image || null;
    }

    appendMessage("bot", replyText, imagePath);
    
    // 재입장 관련 처리: 사용자 메시지나 봇 응답에 재입장 관련 키워드가 있으면 재입장 처리
    const isReentranceMessage = message && (
      message.includes("재입장") || 
      message.includes("다시 입장") ||
      message.includes("우체국에 재입장")
    );
    const isReentranceResponse = replyText && (
      replyText.includes("재입장") || 
      replyText.includes("다시 입장")
    );
    const hasReentranceButton = data.buttons?.some(btn => 
      btn.includes("재입장") || btn.includes("다시 입장")
    );
    
    if ((isReentranceMessage && (isReentranceResponse || hasReentranceButton)) || hasReentranceButton) {
      // 재입장 버튼이 있으면 버튼 클릭을 기다리고, 없으면 바로 재입장 처리
      if (hasReentranceButton) {
        // 버튼이 있으면 버튼 클릭을 기다림 (버튼 클릭 핸들러에서 처리됨)
        if (data.buttons?.length) {
          renderButtons(data.buttons);
          setInputEnabled(false);
        }
      } else {
        // 버튼이 없고 사용자가 재입장을 요청했으면 바로 재입장 처리
        setTimeout(() => {
          reEnterPostOffice();
        }, 500);
      }
    } else {
      if (data.buttons?.length) {
        renderButtons(data.buttons);
        setInputEnabled(false);
      } else setInputEnabled(true);
    }

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
let messageIdCounter = 0;

function appendMessage(sender, text, imageSrc = null, options = {}) {
  const { showAvatar = sender === "bot", avatarSrc = BOT_AVATAR_SRC } = options;
  const messageId = `msg-${messageIdCounter++}`;
  
  // 감정 태그 파싱 (봇 메시지일 경우)
  let processedText = text;
  let emotionImageSrc = null;
  if (sender === "bot") {
    const { emotion, cleanText } = parseEmotionTag(text);
    processedText = cleanText;
    if (emotion) {
      emotionImageSrc = getAvatarForEmotion(emotion);
    }
  }
  const messages = sender === "user" ? [processedText] : splitLongMessage(processedText, 120);

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
      avatarImg.src = BOT_AVATAR_SRC; 
      avatarImg.alt = "부엉장 프로필";
      avatarContainer.appendChild(avatarImg);
      groupElem.appendChild(avatarContainer);
    } else {
      groupElem.classList.add("bot-group-no-avatar");
    }

    const bubbleContainer = document.createElement("div");
    bubbleContainer.classList.add("bot-bubble-container");
    groupElem.appendChild(bubbleContainer);

    // 감정 이미지를 이모티콘처럼 표시 (메시지 앞에)
    if (emotionImageSrc) {
      const emotionImg = document.createElement("img");
      emotionImg.classList.add("emotion-emoji");
      emotionImg.src = emotionImageSrc;
      emotionImg.alt = "감정";
      emotionImg.style.opacity = "0";
      bubbleContainer.appendChild(emotionImg);
      setTimeout(() => {
        emotionImg.style.opacity = "1";
      }, 100);
    }

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
      
      // 우표 텍스트 포맷팅 적용
      const formattedMsg = formatStampText(msg);
      if (formattedMsg !== msg) {
        messageElem.innerHTML = formattedMsg;
      } else {
        messageElem.textContent = msg;
      }
      
      bubbleContainer.appendChild(messageElem);

      setTimeout(() => {
        messageElem.style.opacity = "1";
        
        // 첫 번째 메시지의 너비를 기준으로 다른 메시지들의 max-width 설정
        if (idx === 0 && messages.length > 1) {
          // 약간의 지연을 두고 첫 번째 메시지의 실제 너비 측정
          setTimeout(() => {
            // 임시로 max-width 제거하여 실제 텍스트 너비 측정
            const originalMaxWidth = messageElem.style.maxWidth;
            messageElem.style.maxWidth = 'none';
            const firstMsgWidth = messageElem.offsetWidth;
            messageElem.style.maxWidth = originalMaxWidth || '';
            
            // 같은 그룹의 모든 메시지에 첫 번째 메시지 너비를 max-width로 적용
            const allMessages = bubbleContainer.querySelectorAll('.message.bot');
            allMessages.forEach((elem) => {
              elem.style.maxWidth = `${firstMsgWidth}px`;
            });
          }, 50);
        }
        
        scrollToBottomSmooth();
      }, idx * 500);
    });

    chatLog.appendChild(groupElem);
    return messageId;
  }

  if (sender === "user") {

    const bubbleContainer = document.createElement("div");
    bubbleContainer.classList.add("user-bubble-container");
    
    messages.forEach((msg, idx) => {
      if (!msg) return;
      const messageElem = document.createElement("div");
      messageElem.classList.add("message", sender);
      messageElem.id = `${messageId}-${idx}`;
      messageElem.style.opacity = "0";
      messageElem.textContent = msg;
      bubbleContainer.appendChild(messageElem);

      setTimeout(() => {
        messageElem.style.opacity = "1";
        scrollToBottomSmooth();
      }, idx * 500);
    });
    
    chatLog.appendChild(bubbleContainer);
  } else {
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
      }, idx * 500);
    });
  }

  return messageId;
}

function splitLongMessage(text, maxLen = 100) {
  const result = [];
  
  const quotedParts = [];
  let protectedText = text;

  const quotePatterns = [
    /"[^"]*"/g,        
    /'[^']*'/g,       
    /「[^」]*」/g,      
    /'[^']*'/g,   
    /"[^"]*"/g         
  ];
  
  quotePatterns.forEach((pattern) => {
    protectedText = protectedText.replace(pattern, (match) => {
      const index = quotedParts.length;
      quotedParts.push(match);
      return `__QUOTE_${index}__`;
    });
  });
  
  // 문장 단위로 나눔 (마침표, 물음표, 느낌표 등)
  const sentences = protectedText.split(/(?<=[.?!…~])\s*/);
  
  sentences.forEach((sentence) => {
    sentence = sentence.trim();
    if (!sentence) return;
    
    // 짧은 문장(20자 이하)은 이전 문장과 합치기
    if (sentence.length <= 20 && result.length > 0) {
      const lastIndex = result.length - 1;
      // 합쳐도 maxLen을 넘지 않으면 합치기
      if ((result[lastIndex] + " " + sentence).length <= maxLen) {
        result[lastIndex] += " " + sentence;
      } else {
        result.push(sentence);
      }
    } 
    // 긴 문장은 maxLen 기준으로 나누기
    else if (sentence.length > maxLen && !sentence.includes('__QUOTE_')) {
      let current = "";
      const words = sentence.split(/\s+/);
      words.forEach((word) => {
        if ((current + word).length > maxLen) {
          if (current.trim()) result.push(current.trim());
          current = word + " ";
        } else {
          current += word + " ";
        }
      });
      if (current.trim()) result.push(current.trim());
    } 
    // 적당한 길이의 문장이거나 따옴표가 포함된 문장은 그대로 추가
    else {
      result.push(sentence);
    }
  });
  
  // 플레이스홀더를 원래 따옴표 텍스트로 복원
  const restored = result.map(text => {
    let restored = text;
    quotedParts.forEach((quoted, index) => {
      restored = restored.replace(`__QUOTE_${index}__`, quoted);
    });
    return restored;
  });
  
  return restored.filter(s => s.length > 0);
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

window.addEventListener("load", () => {
  console.log("페이지 로드 완료");
  
  showEntranceMessage();
  setInputEnabled(false);

  setTimeout(() => {
      console.log("초기 메시지 요청");
      sendMessage(true);
    }, 1500);
});
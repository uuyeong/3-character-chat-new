# 🖼️ 이미지 폴더

이 폴더에 챗봇에 사용할 이미지 파일을 추가하세요.

## 📋 필수 파일

### 1. 썸네일 이미지 (필수)
- **파일명**: `thumbnail.png` 또는 `thumbnail.jpg`
- **비율**: 1:1 (정사각형)
- **권장 크기**: 512x512px 이상
- **용도**: 메인 페이지, 상세 페이지에 표시

### 2. 갤러리 이미지 (선택)
- **파일명**: 자유 (예: `photo1.png`, `gallery01.jpg`)
- **비율**: 자유
- **권장 개수**: 5-10개
- **용도**: 채팅 화면의 이미지 갤러리

## 🎨 이미지 준비 방법

### 옵션 1: AI 이미지 생성
- **Midjourney**: https://www.midjourney.com/
- **DALL-E 3**: https://openai.com/dall-e-3
- **Stable Diffusion**: https://stability.ai/

### 옵션 2: 무료 이미지 사이트
- **Unsplash**: https://unsplash.com/
- **Pexels**: https://www.pexels.com/
- **Pixabay**: https://pixabay.com/

### 옵션 3: 직접 제작
- Canva, Figma 등을 사용하여 직접 디자인
- 캐릭터 일러스트 제작
- 관련 장면 촬영

## 📐 이미지 크기 조정

### macOS
```bash
# ImageMagick 설치
brew install imagemagick

# 크기 조정
convert input.jpg -resize 512x512^ -gravity center -extent 512x512 thumbnail.png
```

### Windows
- Paint, Paint 3D 사용
- 또는 온라인 도구: https://www.iloveimg.com/resize-image

### 온라인 도구
- **Remove.bg**: 배경 제거 - https://www.remove.bg/
- **TinyPNG**: 용량 압축 - https://tinypng.com/
- **Squoosh**: 이미지 최적화 - https://squoosh.app/

## ✅ 체크리스트

- [ ] `thumbnail.png` 추가 (1:1 비율)
- [ ] 갤러리 이미지 5개 이상 추가 (선택)
- [ ] 이미지 용량 최적화 (각 1MB 이하 권장)
- [ ] 파일 이름에 한글/공백 사용 안 함
- [ ] config/chatbot_config.json에 썸네일 경로 설정

## 💡 예시

```
static/images/chatbot/
├── thumbnail.png          # 메인 썸네일 (필수)
├── photo1.jpg             # 갤러리 이미지 1
├── photo2.jpg             # 갤러리 이미지 2
├── photo3.jpg             # 갤러리 이미지 3
├── photo4.jpg             # 갤러리 이미지 4
└── photo5.jpg             # 갤러리 이미지 5
```

## 🔗 관련 설정

썸네일 경로는 `config/chatbot_config.json`에서 설정:

```json
{
  "thumbnail": "images/chatbot/thumbnail.png"
}
```

**상세 가이드**: [ASSIGNMENT_GUIDE.md](../../../ASSIGNMENT_GUIDE.md#3️⃣-이미지-준비-30분)

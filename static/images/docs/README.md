# 📸 문서용 이미지

이 폴더는 프로젝트 문서(README, 가이드 등)에 사용되는 이미지를 저장합니다.

## 📁 구조

```
docs/
├── screenshot-main.png         # 메인 페이지 스크린샷
├── screenshot-detail.png       # 상세 페이지 스크린샷
├── screenshot-chat.png         # 채팅 페이지 스크린샷
└── README.md                   # 이 파일
```

## 🖼️ 이미지 추가 방법

1. 스크린샷 촬영
2. 이 폴더에 파일 저장 (`screenshot-*.png`)
3. Markdown 문서에서 참조:

```markdown
![메인 페이지](static/images/docs/screenshot-main.png)
```

또는 상대 경로:

```markdown
![메인 페이지](./static/images/docs/screenshot-main.png)
```

## 📏 권장 사항

- **형식**: PNG (투명 배경 가능) 또는 JPG
- **크기**: 최대 1920px 너비 권장
- **용량**: 각 2MB 이하 권장
- **이름**: `screenshot-{페이지명}.png` 형식

## ✅ 체크리스트

필요한 스크린샷:
- [ ] `screenshot-main.png` - 메인 페이지 (챗봇 목록)
- [ ] `screenshot-detail.png` - 상세 페이지 (챗봇 정보)
- [ ] `screenshot-chat.png` - 채팅 페이지 (대화 화면)

## 🔧 이미지 최적화 (선택)

용량을 줄이려면:

### macOS
```bash
# ImageMagick으로 리사이징
brew install imagemagick
convert input.png -resize 1920x -quality 85 output.png
```

### 온라인 도구
- **TinyPNG**: https://tinypng.com/
- **Squoosh**: https://squoosh.app/

## 📝 Git 관리

이 폴더의 이미지는 Git에 커밋됩니다.
- ✅ 문서용 스크린샷: 커밋 필요
- ❌ 임시 파일: `.gitignore`에 추가

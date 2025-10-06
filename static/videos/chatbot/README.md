# 🎬 비디오 폴더

이 폴더에 챗봇 소개 영상을 추가하세요. (선택 사항)

## 📋 파일 정보

- **파일명**: `video.mp4` (권장)
- **형식**: MP4 (H.264 코덱)
- **길이**: 10-30초 권장
- **크기**: 10MB 이하 권장
- **용도**: 채팅 화면의 영상 보기 버튼

## 🎥 비디오 준비 방법

### 옵션 1: AI 비디오 생성
- **Runway ML**: https://runwayml.com/
- **Pictory**: https://pictory.ai/
- **D-ID**: https://www.d-id.com/

### 옵션 2: 직접 제작
- 스마트폰으로 촬영
- 화면 녹화
- 프레젠테이션 영상

### 옵션 3: 무료 영상 사이트
- **Pexels Videos**: https://www.pexels.com/videos/
- **Pixabay Videos**: https://pixabay.com/videos/
- **Videvo**: https://www.videvo.net/

## 🛠️ 비디오 편집

### 온라인 도구
- **Clipchamp**: https://clipchamp.com/
- **Kapwing**: https://www.kapwing.com/
- **VEED**: https://www.veed.io/

### 변환/압축
```bash
# ffmpeg 설치 (macOS)
brew install ffmpeg

# MP4로 변환
ffmpeg -i input.mov -c:v libx264 -c:a aac video.mp4

# 크기 줄이기
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 -crf 28 video.mp4
```

## 📐 권장 스펙

| 항목 | 권장 값 |
|-----|--------|
| 해상도 | 1280x720 (720p) 이상 |
| 프레임레이트 | 24-30 fps |
| 비트레이트 | 2-5 Mbps |
| 음성 | AAC, 128-192 kbps |
| 길이 | 10-30초 |

## ⚠️ 주의사항

- 파일 크기가 너무 크면 로딩 시간 증가
- Vercel 배포 시 파일 크기 제한 확인 필요
- 저작권 문제가 없는 영상 사용
- 음악 사용 시 저작권 확인

## 💡 영상 아이디어

1. **캐릭터 소개 영상**
   - 챗봇 캐릭터가 자신을 소개
   - 배경, 성격, 특징 설명

2. **사용 가이드 영상**
   - 챗봇 사용 방법 안내
   - 주요 기능 소개

3. **배경 영상**
   - 관련 장소나 풍경
   - 분위기 있는 루프 영상

4. **하이라이트 영상**
   - 주요 기능 시연
   - 대화 예시

## ✅ 체크리스트

- [ ] `video.mp4` 파일 추가
- [ ] 파일 크기 10MB 이하 확인
- [ ] 브라우저에서 재생 테스트
- [ ] 음량 적절한지 확인
- [ ] 저작권 문제 없음 확인

## 🔧 테스트

```bash
# Docker로 실행
docker-compose up

# 브라우저에서 http://localhost:5001/chat 접속
# 🎬 버튼 클릭하여 영상 확인
```

## 📎 참고

영상이 없어도 챗봇은 정상 작동합니다.  
선택 사항이므로 부담 없이 스킵 가능합니다!

**상세 가이드**: [ASSIGNMENT_GUIDE.md](../../../ASSIGNMENT_GUIDE.md)

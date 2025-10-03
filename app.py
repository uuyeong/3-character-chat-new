import os, sys
from flask import Flask, request, render_template, jsonify, url_for, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 초기 화면: 챗봇 선택 페이지
@app.route('/')
def index():
    chatbots = [
        {
            'id': 1,
            'name': '왕도준',
            'image': url_for('static', filename='images/chatbot1/thumbnail.png'),
            'tags': ['#서강대', '#화석선배', '#뻔선', '#캠퍼스']
        },
        {
            'id': 2,
            'name': '은하수 식당',
            'image': url_for('static', filename='images/chatbot2/gallery01.png'),
            'tags': ['#다정남', '#상담캐', '#에겐남', '#미중년', '#존잘']
        },
        {
            'id': 3,
            'name': 'InnerView',
            'image': url_for('static', filename='images/chatbot3/fox.png'),
            'tags': ['#자아탐색', '#모험', '#몽환']
        },
        {
            'id': 4,
            'name': '내 뻔후는 알로스',
            'image': url_for('static', filename='images/chatbot4/thumbnail.png'),
            'tags': ['#알바트로스탑에서_나온', '#전공선택고민', '#캠퍼스_생존기']
        },
        {
            'id': 5,
            'name': 'chatbot5',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            'tags': ['#챗봇', '#유머', '#일상']
        },
        {
            'id': 6,
            'name': 'chatbot6',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            'tags': ['#챗봇', '#유머', '#일상']
        },
        {
            'id': 7,
            'name': 'chatbot7',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            'tags': ['#챗봇', '#유머', '#일상']
        },{
            'id': 8,
            'name': 'chatbot8',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            'tags': ['#챗봇', '#유머', '#일상']
        },{
            'id': 9,
            'name': 'chatbot9',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            'tags': ['#챗봇', '#유머', '#일상']
        }
    ]
    return render_template('index.html', chatbots=chatbots)

# 챗봇 상세정보 페이지 (새로운 HTML로 구현)
@app.route('/detail/<int:bot_id>')
def detail(bot_id):
    chatbot_data = {
       1: {
           "name": "왕도준",
           'image': url_for('static', filename='images/chatbot1/thumbnail.png'),
           "description": "《내 뻔선은 17학번?!》 밥약 신청했을 뿐인데, 17학번 선배가 튀어나왔다?! 어색한 첫 만남, 미묘한 세대 차이, 과연 이 둘의 밥약은 평범하게 끝날 수 있을까?",
           'tags': ['#서강대', '#화석선배', '#뻔선', '#캠퍼스']
       },
       2: {
           "name": "은하수 식당",
            'image': url_for('static', filename='images/chatbot2/gallery01.png'),
            "description": "어서오세요, 밤에만 볼 수 있는 은하수 식당입니다.",
            'tags': ['#다정남', '#상담캐', '#에겐남', '#미중년', '#존잘']
       },
       3: {
           "name": "InnerView",
           'image': url_for('static', filename='images/chatbot3/fox.png'),
           "description": "무의식의 강에서, 당신의 깊은 내면의 욕망을 탐구하세요.<br>당신은 북극여우와 함께 배를 타고,<br>무의식의 강을 천천히 유영합니다.<br>당신의 잠들어 있는 욕망들과<br>그 내면을 담은 유리구슬을 건져보세요.<br><b>made by InnerView",
           'tags': ['#자아탐색', '#모험', '#몽환']
       },
       4: {
           "name": "내 뻔후는 알로스",
           'image': url_for('static', filename='images/chatbot4/thumbnail.png'),
           "description": "서강대의 상징이 인간이 되어 내 후배로 입학했다! 전지적 화석 시점으로 보는 알로 양의 캠퍼스 생존기 — 종강까지 살아남을 수 있을까?",
           'tags': ['#알바트로스탑에서_나온', '#전공선택고민', '#캠퍼스_생존기']
       },
       5: {
            'id': 5,
            'name': 'chatbot5',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            "description": "chatbot5의 설명입니다.",
            'tags': ['#', '#', '#']
        },
        6: {
            'id': 6,
            'name': 'chatbot6',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            "description": "chatbot6의 설명입니다.",
            'tags': ['#', '#', '#']
        },
        7: {
            'id': 7,
            'name': 'chatbot7s',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            "description": "chatbot7의 설명입니다.",
            'tags': ['#', '#', '#']
        },
        8:{
            'id': 8,
            'name': 'chatbot8',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            "description": "chatbot8의 설명입니다.",
            'tags': ['#', '#', '#']
        },
        9: {
            'id': 9,
            'name': 'chatbot9',
            'image': url_for('static', filename='images/hateslop/club_logo.png'),
            "description": "chatbot9의 설명입니다.",
            'tags': ['#', '#', '#']
        }
    }
    bot = chatbot_data.get(bot_id)
    if not bot:
        return "Invalid bot id", 404
    return render_template('chatbot_detail.html', bot=bot, bot_id=bot_id)

# 공용 채팅 화면: URL의 bot_id에 따라 제목 등을 변경
@app.route('/chat/<int:bot_id>')
def chat(bot_id):
    chatbot_names = {
        1: "왕도준",
        2: "은하수 식당",
        3: "InnerView",
        4: "내 뻔후는 알로스",
        5: "chatbot5",
        6: "chatbot6",
        7: "chatbot7",
        8: "chatbot8",
        9: "chatbot9"
    }
    bot_name = chatbot_names.get(bot_id, "챗봇")
    folder_path = f"static/images/chatbot{bot_id}"
    image_files = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith((".png", ".jpg", ".jpeg", ".gif")):
                rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                image_files.append(rel_path.replace("\\", "/"))  # 윈도우 호환
    return render_template('chat.html', bot_id=bot_id, bot_name=bot_name, image_files=image_files)

# API 엔드포인트: 전달된 bot_id에 따라 해당 모듈의 응답 생성 함수를 호출
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    user_message = data.get('message')
    username = data.get('username', '사용자')
    try:
        bot_id = int(data.get('bot_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid bot id'}), 400
    try:
        if bot_id == 1:
            from generation.chatbot1.chatbot1 import generate_response
            reply = generate_response(user_message, username)
        elif bot_id == 2:
            from generation.chatbot2.chatbot2 import generate_response
            reply = generate_response(user_message)
            return jsonify(reply)
        elif bot_id == 3:
            from generation.chatbot3.chatbot3 import generate_response
            reply = generate_response(user_message)
        elif bot_id == 4:
            from generation.chatbot4.chatbot4 import generate_response
            reply = generate_response(user_message)
            return jsonify(reply)
        elif bot_id == 5:
            from generation.chatbot5.chatbot5 import generate_response
            reply = generate_response(user_message)
        elif bot_id == 6:
            from generation.chatbot6.chatbot6 import generate_response
            reply = generate_response(user_message)
        elif bot_id == 7:
            from generation.chatbot7.chatbot7 import generate_response
            reply = generate_response(user_message)
        elif bot_id == 8:
            from generation.chatbot8.chatbot8 import generate_response
            reply = generate_response(user_message)
        elif bot_id == 9:
            from generation.chatbot9.chatbot9 import generate_response
            reply = generate_response(user_message)
        else:
            return jsonify({'error': 'Invalid bot id'}), 400

        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

from bson import ObjectId
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from bs4 import BeautifulSoup

import certifi
ca = certifi.where()
from bson.json_util import dumps

import jwt
import datetime
import hashlib

from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from pymongo import MongoClient
client = MongoClient('mongodb+srv://yewonkim:sjgkxn13@cluster0.v9e9u.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


# 로그인시 로그인 페이지로 넘어감
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

# 로그인 서버
# 로그인 창,로그인 성공,실패, 토큰유지2시간
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')#.decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 아이디 중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

# 회원가입
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          #프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})



#메인페이지
#크롤링 데이터 저장, 불러오기
@app.route('/', methods=['GET'])
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        data = requests.get('https://www.goodchoice.kr/product/result?keyword=%EA%B0%95%EC%9B%90', headers=headers)
        soup = BeautifulSoup(data.text, 'html.parser')

        trs = soup.select('#poduct_list_area > ul > li')

        hotels = []
        for tr in trs:
            hotel_name = tr.select_one('a > div > div.name > strong').text.strip()
            location = tr.select_one('a > div > div.name > p:nth-child(3)').text.strip()
            hotel_img = tr.select_one('a > p > img')['data-original'].lstrip('/')
            detail_url = tr.select_one('a')['href']

            hotel = {
                'hotel_img': hotel_img,
                'hotel_name': hotel_name,
                'location': location,
                'detail_url': detail_url,
                'owner_comment': '',
                'comments': []
            }
            # db.hotels.insert_one(hotel)
        hotels = list(db.hotels.find({}, {'_id': False}))
        return render_template('index.html', user_info=user_info, hotels=hotels )

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))



#상세페이지
#클릭한 호텔명과 같은 url로 이동, 사장님 코멘트 크롤링 해서 저장하기
@app.route('/detail', methods=['GET'])
def detail():
    hotel_name = request.args.get('hotel_name', type=str)
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})

    #클릭한 호텔명과 같은 url에서 사장님 코멘트 크롤링
    detail_url = db.hotels.find_one({'hotel_name':hotel_name})['detail_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(detail_url, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    get_owner_comment = soup.select_one('#content > div.top > div.right > div.comment > div').text
    find_owner_comment = db.hotels.find_one({'detail_url': detail_url})['owner_comment']

    #db의 사장님 코멘트가 비어 있으면 저장한 후에 코멘트 불러온다.
    if find_owner_comment == '':
        db.hotels.update_one({'detail_url': detail_url}, {'$set': {'owner_comment': get_owner_comment}})
        hotel_info = db.hotels.find_one({'detail_url': detail_url})
    #아니면 코멘트만 불러온다
    else:
        hotel_info = db.hotels.find_one({'detail_url': detail_url})
    return render_template('detail.html', user_info=user_info, hotel_info=hotel_info)


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    hotel_name = request.form['hotel_name']
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]

        #hotels db comments 필드에 댓글 관련 데이터 삽입
        db.hotels.update_one({'hotel_name':hotel_name}, {'$push': {'comments':{
            '_id': ObjectId(),
            'username':user_info['profile_name'],
            'comment':comment_receive,
            'date':date_receive
        }}})

        return jsonify({"result": "success", 'msg': '업로드 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    hotel_name = request.args.get('hotel_name')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # comments 필드만 찾아서 넘겨준다.
        posts = db.hotels.find_one({'hotel_name': hotel_name})["comments"]
        #print(posts)

        return jsonify({'posts': dumps(posts)})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        post_id_receive = request.form["post_id_give"]
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]

        doc = {
            "post_id": post_id_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]

        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"/{username}.{extension}"
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set': new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))




if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template, request, jsonify, redirect, url_for
app = Flask(__name__)
import requests
from bs4 import BeautifulSoup
import jwt

from pymongo import MongoClient
client = MongoClient('mongodb+srv://yewonkim:sjgkxn13@cluster0.v9e9u.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta




@app.route('/', methods=['GET'])
def main():
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
        # owner_comment = tr.select_one('#content > div.top > div.right > div.comment > div').text

        hotel = {
            'id':'',
            'pw':'',
            'name':'',
            'hotel_imgs': [hotel_img],
            'hotel_name': hotel_name,
            'location': location,
            'detail_url': detail_url,
            'like': 0,
            'comments':'',
            'owner_comment': ''
        }
        # db.hotels.insert_one(hotel)
    hotels = list(db.hotels.find({}, {'_id': False}))

    return render_template('index.html', hotels = hotels)


@app.route('/detail', methods=['GET'])
def detail():
    hotel_name = request.args.get('hotel_name', type=str)
    detail_url = db.hotels.find_one({'hotel_name':hotel_name})['detail_url']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(detail_url, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    get_owner_comment = soup.select_one('#content > div.top > div.right > div.comment > div').text
    find_owner_comment = db.hotels.find_one({'detail_url': detail_url})['owner_comment']

    hotel_img = db.hotels.find_one({'detail_url': detail_url})['hotel_img']
    hotel_name = db.hotels.find_one({'detail_url': detail_url})['hotel_name']
    location = db.hotels.find_one({'detail_url': detail_url})['location']
    like = db.hotels.find_one({'detail_url': detail_url})['like']

    if find_owner_comment == '':
        db.hotels.update_one({'detail_url': detail_url}, {'$set': {'owner_comment': get_owner_comment}})
        owner_comment = db.hotels.find_one({'detail_url': detail_url})['owner_comment']
    else:
        owner_comment = db.hotels.find_one({'detail_url': detail_url})['owner_comment']
    return render_template('detail.html', owner_comment=owner_comment, hotel_img=hotel_img, hotel_name=hotel_name, location=location, like=like)


# # 좋아요 업데이트
# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_recieve = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_recieve, SECRET_KEY, algorithms=['HS256'])
#
#         user_info = db.users.find_one({"username": payload["id"]})
#         post_id_receive = request.form["post_id_give"]
#         type_receive = request.form["type_give"]
#         action_receive = request.form["action_give"]
#         doc = {
#             "post_id": post_id_receive,
#             "username": user_info["username"],
#             "type": type_receive
#         }
#         if action_receive == "like":
#             db.likes.insert_one(doc)
#         else:
#             db.likes.delete_one(doc)
#         count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
#         return jsonify({"result": "success", 'msg': 'updated', "count": count})
#
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))

#로그인 페이지
# @app.route('/sign_in', methods=['GET'])
# def sign_in():
#     return render_template('sign_in.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
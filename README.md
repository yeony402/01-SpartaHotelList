# project01-SpartaHotelList
* **flask / js / ajax / mongoDB** 로 구현한 팀프로젝트

1. 회원가입과 로그인 기능 구현
2. 여기어때에서 크롤링한 호텔정보 목록 메인페이지에 나타내기
3. 마이페이지에서 프로필 이미지, 닉네임, 자기소개 수정
4. 호텔정보 상세페이지에 댓글 기능, 좋아요 기능 추가

![image](https://user-images.githubusercontent.com/44489399/188081791-fb494c6c-6553-41ee-a305-6c8dd18b5510.png)

![image](https://user-images.githubusercontent.com/44489399/188082071-9f5ea311-32df-4175-9195-a422113702a0.png)


- 게시글과 댓글 컬렉션이 매칭되지 않아 모든 게시글에 같은 댓글이 보이는 현상   
->  게시글 컬렉션에 subdocument를 만들어서 해결

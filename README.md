# **실제 웹사이트에서 이루어지는 로그인 성능 및 보안 개선 프로젝트**

---

## **목차**

**1\. 프로젝트 소개**  
**2\. 프로젝트 제작 과정**  
**3\. 프로젝트 성능 및 보안 향상**  
**4\. 분석**

---

## **프로젝트 소개**

 실제 네이버, 다음, 각종 웹사이트에서 이루어지는 **로그인 프로그램**을 구현하는 프로젝트입니다. 단순히 로그인 기능을 구현하는 것이 아니라, 프레임워크를 따로 사용하지 않고 MySQL과 라이브러리만을 사용하여 로그인을 할 때 발생하는 **성능 문제** 및 **보안 문제**를 파악하는 것을 중시했습니다.

 로그인을 할 때, 어떤 요소가 성능을 낮추는지에 대해 생각을 하며 코드를 구현했습니다. 서버에 장애가 일어날만한 요소를 고려해본 결과, 트래픽이 부하될 경우, 로그인을 할 때 발생하는 다중 해시 처리에서 적어도 성능에 영향을 미칠 것임을 이용하여 해결방법을 찾았습니다. 단일 스레드 환경에서도 병렬 처리가 가능한 **비동기적 해시 처리** 기법으로 해결했습니다.

 사용자가 많이 사용할 수 밖에 없어 성능이 향상되어야 하는 기능이긴 하오나, 개인 정보를 저장하는 기능이기 때문에, 보안 관련 문제를 더욱 개선해야한다고 생각했습니다. 비밀번호가 해싱이 되는 것만으로는, 충분히 복호화할 수 있다고 생각하여 SQL인젝션을 방지하기 위해 **쿼리를 매개변수화**했습니다.

---

## **프로젝트 제작 과정**

### **사용 기술**

-   Python
-   SQLite3
-   MySQL
-   라이브러리 : hashlib, getpass, mysql-connect, asyncio, concurrent.futures

### **1\. 해시 함수 구현**

```
def hash_password(password):
    hash_object = hashlib.sha256()
    hash_object.update(password.encode('utf-8'))
    return hash_object.hexdigest()
```

 입력 받은 비밀번호를 **UTF-8**로 인코딩 후, **SHA-256** 해싱 알고리즘을 사용하여 암호화하고, 64자의 16진수 문자열인 **hexdecimal string**으로 반환합니다.

### **2\. 데이터베이스 연결**

```
def create_connection():
    try:
        conn = db.connect(
            host="127.0.0.1",
            port="2406",
            user="root", 
            password="root", 
            database="login_db",
            auth_plugin='mysql_native_password'
        )
        return conn
    except db.Error as err:
        print(err)
    return None
```

 SQL 서버에 접속하는 함수이오나, mysql 접근 권한을 얻기 위해 mysql\_native\_password 를 사용했습니다.

### **3\. 회원가입 함수**

```
def register(conn, username, password):
    hashed_password = hash_password(password)
    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username, hashed_password))
        conn.commit()
        cursor.close() 
        print(f"'{username}' has been registered.")
    except db.Error as err:
        print(err)
```

### **4\. 로그인 함수**

```
def login(conn, username, password):
    sql = "SELECT password FROM users WHERE username = %s"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username))
        result = cursor.fetchone()
        cursor.close()
        if result:
            hashed_password = result[0]
            if hash_password(password) == hashed_password:
                print("You have been logged in.")
            else:
                print("Incorrect password.")
        else:
            print("User not found.")
    except db.Error as err:
        print(err)
```

 **fetchone()** 은 SQL Query 실행 후, 결과 집합의 한 행을 가져오는 함수입니다. 한 행이 **NULL**이라면 **NONE**을 리턴하므로 조건문으로 값 유무 확인 후, **username**을 기준으로 데이터베이스에서 비밀번호를 가져와 해시된 비밀번호와 비교합니다.

---

## **프로젝트 성능 및 보안 향상**

### **1\. 비동기적 해시 처리**

```
async def hash_password(password):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hashlib.sha256, password.encode('utf-8')).hexdigest()
async def register(conn, username, password): 
    ...
async def login(conn, username, password):
    ...
async def main():
    ...
```

 여러 사용자의 비밀번호 해시를 동시에 처리하는 작업 처리 기법입니다. 트래픽이 많은 웹사이트에는 필수적인 기능입니다. **asyncio** 라이브러리를 통해 **해시 함수, 회원가입 함수, 로그인 함수, 메인 함수**를 비동기적으로 변경했고, 해시 처리가 일정한 주기로 다수의 비동기 작업을 동시에 처리하는 **이벤트 루프**를 추가했습니다.

### **2\. 쿼리 매개변수화(Parameterized Query)**

```
async def login(conn, username, password):
    sql = "SELECT password FROM users WHERE username = %s"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        cursor.close() 
        if result:
            hashed_password = result[0]
            if await hash_password(password) == hashed_password:
                print("You have been logged in.")
            else:
                print("Incorrect password.")
        else:
            print("User not found.")
    except db.Error as err:
        print(err)
```

 매개변수화된 쿼리는 **cursor.execute(sql, (username,))** 쿼리와 데이터를 구분하여 처리합니다. 구체적으로, username 뒤에 '콤마'가 존재하지 않는 경우, username에 악의적인 사용자가 **_admin' OR '1' = '1' --_** 라고 작성할 경우에는, 1=1은 항상 참이기 때문에 모든 유저의 비밀번호를 조회를 할 수 있게됩니다. 이 후, -- 주석처리를 통해 그 뒤의 모든 쿼리는 무시됩니다. 이러한 SQL 인젝션을 방지하기 위해 (username,) 의 튜플 형태로 만들었습니다.

---

## **분석**

<div align="center">
  <img src="https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fy4MOc%2FbtsIjLsybjm%2F0Nz6kvLKhtKCPP4EnPhkWk%2Fimg.png" alt="회원가입">
</div>

<그림 1> 처럼 root라는 아이디로 회원가입을 했습니다. 비밀번호는 getpass 라이브러리를 통해 보이지 않도록 구현했습니다.

---

<div align="center">
  <img src="https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FylQxt%2FbtsIiVPYYWH%2F2yhYgJBeZ3E9Pzlw2PuUnk%2Fimg.png" alt="데이터베이스 저장">
</div>

<그림 2. 데이터베이스 저장> 데이터베이스 login_db에 root 사용자 이름과 해시된 비밀번호가 잘 저장되어있는 것을 볼 수 있습니다.

---

<div align="center">
  <img src="https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FkD7up%2FbtsIicdG18V%2FBaf55o96G3l9SHiBhVK681%2Fimg.png" alt="SQL 인젝션 방지">
</div>

<그림 3. SQL 인젝션 방지> **SQL 인젝션**을 성공적으로 방지하고 있는 것을 볼 수 있습니다.

 실제 웹 사이트에는 트래픽이 어느 순간에 급증할 수도 있고, 개인정보가 유출될 가능성이 존재하기 때문에, 로그인 기능에서 가장 중요히 생각하는 요소는 효율성과 안전성일 수 밖에 없습니다. SQL 인젝션과 비동기적 처리 함수 이용은 필연적입니다.

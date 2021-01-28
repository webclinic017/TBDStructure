# TDB Structure

## 자동매매툴 (실제/백테스팅 매매 지원)

키움, 이베스트, 바이낸스 등 API를 활용하여 실제 매매와 백테스팅을 진행할 수 있는 프로그램


### 용어 설명:

TBD툴은 큐를 활용하여 여러 프로세스 사이의 소통을 관리한다.

1. data_queue: data queue를 통해서 Strategy, Portfolio는 마켓 이벤트를 전송 받는다.

2. port_queue: port_queue는 여러 클래스로부터 이벤트를 받아 각 이벤트에 맞게 처리한다.
               모든 이벤트는 결국 실제 매매나 포트폴리오 정보의 업데이트가 필요하기 때문에 필요하다.

3. api_queue: api_queue는 API와 DataHandler의 연결을 해준다. API(키움, 이베스트, 바이낸스)에서 발생하는 실시간 데이터를
              DataHandler로 보내어주어 shared_memory를 만들게 해주기 위함이다.

4. order_queue: 키움과 같은 툴은 한 계정으로 하나의 프로그램(창)밖에 사용하지 못하기 때문에
                Portfolio/Execution에서 보내오는 order 이벤트를 order_queue에서 받아서 처리해준다.
   

추가로, shared_memory는 DataHandler에서 만들고 그 정보를 Strategy로 보내 주어:

- self.tick_mem_array
- self.hoga_mem_array
- self.min_mem_array

로 사용할 수 있도록 해준다.
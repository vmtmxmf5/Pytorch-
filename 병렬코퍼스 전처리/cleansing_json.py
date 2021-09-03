def clean_lng(sentence, unicode):
    '''
    문장 전처리 함수
    문장과 해당 언어의 유니코드를 문자열로 넣으면 된다
    '''
    if type(sentence) == str:
        p = re.compile(fr'''
        (
        ((http|https)\:\/\/)?            # http가 존재하거나 존재하지 않거나
        [a-zA-Z0-9\.\-_]+\.              # 웹주소 .kr 이전 까지만 선택
        ([a-zA-Z]){2,6}                  # .kr, .org 등을 모두 선택
        ([a-zA-Z0-9\.\&\/\?\:@\-_=#])*   # 파라미터 선택 / 이메일 선택
        )|
        (
        \([^)]*\)                        # () 안에 내용까지 선택 (반각)
        )|
        (
        \<[^>]*\>                        # <> 안에 내용까지 선택 (반각)
        )|
        (
        \[[^\]]*\]                       # [] 안에 내용까지 선택 (반각)
        )|
        (
        --[^-]*--                        # -- 내용 -- 내용까지 선택 (반각)
        )|
        (
        \u00ab[^\u00bb]*\u00bb           # <> 안에 내용까지 선택 (반각)
        )|
        (
        \uff1c[^\uff1e]*\uff1e           # < > 안에 내용까지 선택 (전각)
        )|
        (
        \ufe64[^\ufe65]*\ufe65           # << >> 안에 내용까지 선택 (전각)
        )|
        (
        \uff08[^\uff09]*\uff09           # () 안에 내용까지 선택 (전각)
        )|
        (
        \ufe59[^\ufe5a]*\ufe5a            # () 안에 내용까지 선택 (전각)
        )|
        (
        \uff3b[^\uff3d]*\uff3d           # [] 안에 내용까지 선택 (전각)
        )|
        (
        [^ {unicode}|  # 사용할 언어

        0-9|0-9 /|0-9/|0-9 :|0-9:|       # 숫자와 숫자 뒤 /와 :는 선택에서 제외

        ·|.|,|!|?|"|"|'|⸢|⸥|。|          # 포함할 특수문자 (반각)
                                         # 포함할 특수문자 (전각) :
        \uff0e|\ufe52|\uff0c|\ufe51|     # 마침표, 콤마, 느낌표,
        \ufe50|\ufe57|\uff01|\ufe15|     # 물음표, 큰따옴표,
        \uff1f|\ufe56|\ufe16|\uff02|     # 어퍼스트로피, 꺽새 (전각)
        \uff07|\ufe41|\ufe42|\ufe43|\ufe44]
        )
        ''', re.VERBOSE)
        result = p.sub('', sentence)
    else:
        result = ''
    return result


def cleansing_data(chunk_data, q, pid):
    '''
    chunk json 넣어주시면 전처리해서 새로운 OrderedDict를 반환합니다
    '''
    # 동북 아시아
    ko = '\u3131-\u3163|\uac00-\ud7af'    # ko
    zh = '\u4e00-\u62ff|\u6300-\u77ff|\u7800-\u8cff|\u8d00-\u9fff' # zh_cn
    ja = '\u3041-\u3096|\u30a0-\u30ff|\u3400-\u4db5|\u4e00-\u9fcb|\uf900-\ufa6a'  #ja

    # 러시아
    ru = '\u0410-\u044f'                 # ru

    # 유럽 / 미국 (vi, de, pt, fr, id, es, it, en)
    for country in 'vi,de,pt,fr,id,es,it,en'.split(','):
        locals()[f'{country}'] = '\u0041-\u007a|\u00c0-\u0178|\u1e00-\u1eff|\u0180-\u024f|\u1e00—\u1eff|\u0027'

    # 인도
    hi = '\u0900-\u097f|\ua8e0-\ua8ff' # hi (드 파나 가리어)

    # 아랍
    ar = '\u0627-\u064a'               # ar
    
    new = []
    for line in chunk_data:
        new_line = OrderedDict()
        src_unicode = locals()[line['src_lang']]
        tgt_unicode = locals()[line['tgt_lang']]

        new_line['src_lang'] = line['src_lang']
        new_line['src_text_raw'] = line['src_text_raw']
        new_line['src_text'] = clean_lng(line['src_text_raw'], src_unicode)

        new_line['tgt_lang'] = line['tgt_lang']
        new_line['tgt_text_raw'] = line['tgt_text_raw']
        new_line['tgt_text'] = clean_lng(line['tgt_text_raw'], tgt_unicode)

        new_line['origin'] = line['origin']
        new_line['domain'] = line['domain']
        new.append(new_line)
    q.put(new)
    print(pid, '현재 queue에 쌓인 개수: ', q.qsize())
    #return new

def dump_queue(q):
    """
    queue 데이터를 모두 list로 바꿔줌
    """
    q.put('STOP')
    result = []
    for j in iter(q.get, 'STOP'):
        result.append(j)
    return result

def wait_until(cond1, cond2, timeout, period=0.25):
    end = time.time() + timeout
    while time.time() < end:
        if cond1 == cond2:
            return True
        time.sleep(period)
    return False


import multiprocessing
import time
import json
import re
from collections import OrderedDict

if __name__ == '__main__':
    startTime = float(time.time())

    workers, last_files = 4, 4
    q = multiprocessing.Queue() # shared queue
    path = 'C:/Users/CPB06GameN/글을쓰자/PyTorch-master/연습폴더/final_chunk'
    
    processes = []
    for i in range(last_files):
        with open(path + f'/final_{i}.json', 'r', encoding='utf-8') as f:
            json_file = json.load(f, object_pairs_hook=OrderedDict)
        sub_process = []
        for p_start in range(0, workers):
            p_num = ['1st', '2nd', '3rd', '4th']
            p = multiprocessing.Process(target=cleansing_data,
                                        args=(json_file[p_start::workers], q, p_num[p_start]))
            processes.append(p)
            sub_process.append(p)
        for p in sub_process:
            p.start()
    # main process가 마지막 queue를 가져감, qsize 조건문을 걸자     
    wait_until(q.qsize(), workers*last_files, 10)
    fin = dump_queue(q)
    print(len(fin[15])) # worker 1명이 처리한 데이터 개수

    q.close()
    q.join_thread()

    # main 프로세스가 sub 프로세스가 끝날 때 까지 기다린다 == join()
    for p in processes:
        p.terminate()
        p.join()

    endTime = float(time.time())
    print("총 작업 시간", (endTime - startTime))
  
# 6.415초 => 2.272초

# files = os.listdir(path)
# for idx in range(len(files)):
#     with open(path + f'/final_{idx}.json', 'r', encoding='utf-8') as f:
#         data = json.load(f, object_pairs_hook=OrderedDict)
#     cleansing_json = cleansing_data(data)
#     print(cleansing_json)

import random
import json
import os
import time
import multiprocessing
from multiprocessing import Process, JoinableQueue

bank_codes = {}
bank_codes["Fio"] = 2010

def_params = {
    "repeated_bonus": 0.6,
    "same_bonus": 0.6,
    "asc_bonus": 0.7,
    "desc_bonus": 0.7,

    "symmetry_bonus": 0.5,
    "reversed_symmetry_bonus": 0.5,
}
def verify_number(acc_number, strict=True):
    num = [int(i) for i in str(acc_number)]
    if(len(num)>10 or len(num)<8):
        return False
        #raise Exception("Account number must be 8-10 digits long")
    if(strict and len(num)==10 and num[0] in {1, 2, 9}):
        return False #Fio restrictions
    S = 1*num[-1] + 2*num[-2] + 4*num[-3] + 8*num[-4] + 5*num[-5] + 10*num[-6] + 9*num[-7] + 7*num[-8]
    if(len(num)>8):
        S += 3*num[-9]
    if (len(num)>9):
        S += 6 * num[-10]
    if(S%11==0):
        return True
    else:
        return False

def number_cost(acc_number, bank_number="", params=None):
    _params = dict(def_params)
    if(params!=None):
        _params.update(params)
    num = [int(i) for i in str(acc_number)]
    cum_cost = 0
    used_digits = set()
    prev_digit = None
    asc_serie = 0
    desc_serie = 0
    for i in range(len(num)):
        digit = num[i]
        cost = 1.0

        if(digit in used_digits):
            cost *= _params["repeated_bonus"]
        if(prev_digit!=None):
            if(digit==prev_digit):
                cost *= _params["same_bonus"]
            if(digit==(prev_digit-1)%10):
                desc_serie += 1
            else:
                desc_serie = 0
            if (digit == (prev_digit+1)%10):
                asc_serie += 1
            else:
                asc_serie = 0
            cost = cost * _params["asc_bonus"]**asc_serie
            cost = cost * _params["desc_bonus"] ** desc_serie
        used_digits.add(digit)
        prev_digit = digit
        cum_cost += cost
    half_len = len(acc_number) // 2
    #repetition
    if (acc_number[0:half_len] == acc_number[half_len:]):
        cum_cost *= _params["symmetry_bonus"]
    #symmetry
    if(acc_number[0:half_len] == acc_number[-1:-half_len-1:-1]):
        cum_cost *= _params["reversed_symmetry_bonus"]
    return cum_cost

def process_interval(start, end, params, max_cost=float('Inf')):
    ret = []
    for acc_n in range(start, end):
        if(not verify_number(acc_n)):
            continue
        acc_cost = number_cost(acc_n, params=params)
        if(acc_cost<max_cost):
            ret.append((acc_cost, acc_n))
    return ret

def worker(input_queue, output_queue):
    print("Worker started")
    time.sleep(10)
    while not input_queue.empty():
        interval = input_queue.get()
        start = interval[0]
        end = interval[1]
        print("Processing %d %d" % (start, end))
        for acc_num in range(start, end):
            cost = number_cost(str(acc_num))
        input_queue.task_done()
    print("Worker finished")

if __name__ == "__main__":
    max_accepted_cost = 9999999999
    max_candidates = 500000
    clean_coef = 1.1
    candidates = []
    preload = []
    considered = 0
    valid = 0

    acc_group_size = 100000
    start_acc = 10000000
    #last_acc = 10000000000
    last_acc = 11000000

    cpu_count = multiprocessing.cpu_count()
    processes = []

    input_queue = JoinableQueue()
    output_queue = JoinableQueue()
    #insert intervals to check
    i=start_acc
    while i<last_acc:
        i_start = i
        i_end = min(i + acc_group_size, last_acc)
        interval=(i_start, i_end)
        input_queue.put(interval)
        #print("Interval %d %d" % (i_start, i_end))
        i = i_end
    #input_queue.close()
    #create and start working processes
    for i in range(0, cpu_count):
        p = Process(target=worker, args=(input_queue, output_queue))
        p.start()
        processes.append(p)
    #wait for work to be finished
    input_queue.join()
    exit()

    print("Program run")
    for acc_n in range(10000000, 10000000000):
        considered += 1
        if(not verify_number(acc_n)):
            continue
        valid += 1
        acc_cost = number_cost(acc_n)
        if(acc_cost<max_accepted_cost):
            candidates.append((acc_cost, acc_n,))
        if(len(candidates)>max_candidates*clean_coef):
            candidates = sorted(candidates, key=lambda candidates: candidates[0])
            candidates = candidates[0:max_candidates]
            max_accepted_cost = candidates[-1][0]
            print("Candidates considered:%d" % (considered,))
            print("Valid candidates:%d" % (valid,))
            print("Best cost:%f for candidate:%d" % (candidates[0][0], candidates[0][1]))
            #print(candidates)
            with open(tmp_output, 'w') as f:
                json.dump(candidates, f)
                f.close()
            print("OK")

    with open(tmp_output, 'w') as f:
        json.dump(candidates, f)
        f.close()

    print("LIST START")
    for num in candidates:
        print("%d" % (num[1]))
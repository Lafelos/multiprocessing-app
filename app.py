from flask import Flask, request, jsonify
import threading
import multiprocessing
import time
import queue

app = Flask(__name__)

def cpu_bound_task(n):
    return sum(i * i for i in range(n))

def thread_worker(task_queue, results):
    while True:
        try:
            n = task_queue.get_nowait()
        except queue.Empty:
            break
        results.append(cpu_bound_task(n))

def process_worker(job_queue, result_list):
    while True:
        n = job_queue.get()
        if n is None:
            break
        result_list.append(cpu_bound_task(n))

def run_threading(tasks, num_workers):
    q = queue.Queue()
    for t in tasks:
        q.put(t)
    results = []
    start = time.time()
    threads = [threading.Thread(target=thread_worker, args=(q, results))
               for _ in range(num_workers)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return time.time() - start, len(results)

def run_multiprocessing(tasks, num_workers):
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    result_list = manager.list()

    #Stack Data and put add an end.
    for t in tasks:
        job_queue.put(t)
    for _ in range(num_workers):
        job_queue.put(None)

    #Create Processes
    processes = [multiprocessing.Process(target=process_worker, args=(job_queue, result_list))
                 for _ in range(num_workers)]
    start = time.time()
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    duration = time.time() - start
    return duration, len(result_list)

@app.route('/generar', methods=['GET'])
def generar_elementos():
    try:
        NUM_TASKS = int(request.args.get('numTask', 0))
        TASK_SIZE = int(request.args.get('numSize', 0))

        if NUM_TASKS <= 0 and TASK_SIZE <= 0:
            return jsonify({'error': 'La cantidad debe ser mayor que 0'}), 400
        
        NUM_WORKERS = multiprocessing.cpu_count()

        tasks = [TASK_SIZE] * NUM_TASKS
        total = NUM_TASKS * TASK_SIZE

        #Sequential
        t0 = time.time()
        seq = [cpu_bound_task(n) for n in tasks]
        seq_time = time.time() - t0

        #Threading
        th_time, th_count = run_threading(tasks, NUM_WORKERS)

        #Multiprocessing
        mp_time, mp_count = run_multiprocessing(tasks, NUM_WORKERS)

        return jsonify({
            'Sequential':      {'Time': round(seq_time, 2), 'Results': len(seq)},
            'Threading':       {'Time': round(th_time, 2), 'Results': th_count},
            'Multiprocessing': {'Time': round(mp_time, 2), 'Results': mp_count},
            'Total_Processed_Elements': total,
            'Used_Processes': NUM_WORKERS
        }), 200

    except ValueError:
        return jsonify({'error': 'Parámetro "cantidad" inválido'}), 400



if __name__ == '__main__':
    app.run(debug=True)

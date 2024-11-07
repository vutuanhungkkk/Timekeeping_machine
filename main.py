import multiprocessing
import jet
import web

def run_jetson():
    jet.main()

def run_web():
    web.main()

if __name__ == '__main__':
    jetson_process = multiprocessing.Process(target=run_jetson)
    web_process = multiprocessing.Process(target=run_web)

    # Start processes
    jetson_process.start()
    web_process.start()

    # Join processes to wait for them to complete
    jetson_process.join()
    web_process.join()

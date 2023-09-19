
import os
import sys
import subprocess
import time

LOG_FILENAME = "log.txt"


def log(logString):
    '''
    log function
    writes information with timestamp in the current folder
    :param logString: content to write
    :return: nothing
    '''

    localtime_ = time.localtime()
    t = time.strftime("%d/%m/%Y %H:%M:%S", localtime_)
    try:
        f = open(LOG_FILENAME, "a")
        f.write(t + " : " + str(logString) + '\n')
        f.close()
        print(str(logString))
    except:
        print(str(logString))

def moduleAvailable():
    available = True
    try:
      import pyaedt
    except ImportError:
      available = False

    return available


def main():
    currentWkDir = os.getcwd()
    curScript = sys.argv[1]
    curInputFile = sys.argv[2]
    curInputFile_1 = sys.argv[3]
    python_exe_loc = sys.argv[4]
    log('args                 : ' + str(sys.argv))
    log('current dir          : ' + currentWkDir)
    log('current script       : ' + curScript)
    log('input file           : ' + curInputFile)
    log('additional file      : ' + curInputFile_1)
    log('Python exe location  : ' + os.path.join(python_exe_loc,"python.exe"))
    curInputFile_1 = curInputFile_1.split("\\")[0]

    app_data_path = os.environ["APPDATA"]
    env_pyaedt = os.path.join(app_data_path, "pyaedt_env_ide")

    if not os.path.exists(env_pyaedt):
        subprocess.call([os.path.join(python_exe_loc,"python.exe"), "-m", "venv", env_pyaedt])
        subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "install", "pyaedt"])
        subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "install", "ipython", "-U"])

    else:
        if not os.path.exists(os.path.join(env_pyaedt,"Lib","site-packages","pyaedt")):
            subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "-m", "pip", "install", "--upgrade", "pip"])
            subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "install", "pyaedt"])
            subprocess.call([os.path.join(env_pyaedt, "Scripts", "pip"), "install", "ipython", "-U"])

    try:
        log('launching Quick SI analysis with ' + curInputFile)
        subprocess.call([os.path.join(env_pyaedt, "Scripts", "python.exe"),curScript, curInputFile, curInputFile_1])

    except:
        log('failed launching app')
    time.sleep(60)

    # modify dates of files
    modifyModificationDate(["*.prt*", "*.asm*"])

    log("end.")
    # check if parametric is running:
    # pollAppRunning("parametric.exe")


def modifyModificationDate(extensionsList):
    import glob
    newModTime = time.time()  # new modification time will be current time

    for ext in extensionsList:
        for file in glob.glob(ext):
            os.utime(file, (newModTime, newModTime))

    return True


def pollAppRunning(process):
    # parameters
    inital_sleep = 5  # waits 10 secs before starting the loop to make sure process is running
    timeout = 3600  # 1 hour max
    time_interval = 2  # time interval used to check the application existence

    log("Waiting for app to launch...")
    time.sleep(inital_sleep)
    counter = 0
    log("Starting loop...")
    while is_already_running(process) and ((counter * time_interval) < timeout):
        time.sleep(time_interval)
        counter += 1
        log("loop #" + counter)
    return True


def get_running_processes(look_for=''):
    import re
    from subprocess import Popen, PIPE, DEVNULL
    # edited from https://stackoverflow.com/a/22914414/7732434
    cmd = f'tasklist /NH /FI "IMAGENAME eq {look_for}"'
    p = Popen(cmd, shell=True, stdout=PIPE, stdin=DEVNULL, stderr=DEVNULL, text=True)
    task = p.stdout.readline()
    while task != '':
        task = p.stdout.readline().strip()
        m = re.match(r'(.+?) +(\d+) (.+?) +(\d+) +(\d+.* K).*', task)
        if m is not None:
            process = {'name': m.group(1), 'pid': m.group(2), 'session_name': m.group(3),
                       'session_num': m.group(4), 'mem_usage': m.group(5)}
            yield process


def is_already_running(program_name, threshold=1):
    for process in get_running_processes(program_name):
        process_name = process['name']
        if process_name == program_name:
            threshold -= 1
            if threshold < 0: return True
    return False


main()
log('end of script')







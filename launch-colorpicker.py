import subprocess
import time
import ctypes
import os
import sys

User32 = ctypes.windll.user32
Kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))

def get_window_pid(hwnd):
    pid = ctypes.c_uint()
    User32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def is_window_visible(hwnd):
    return User32.IsWindowVisible(hwnd)

def get_class_name(hwnd):
    buff = ctypes.create_unicode_buffer(256)
    User32.GetClassNameW(hwnd, buff, 256)
    return buff.value

def is_wrapper_active(target_pid):
    found = [False]
    
    def enum_handler(hwnd, lParam):
        if get_window_pid(hwnd) == target_pid:
            if is_window_visible(hwnd):
                if "HwndWrapper" in get_class_name(hwnd):
                    found[0] = True
                    return False
        return True

    User32.EnumWindows(WNDENUMPROC(enum_handler), 0)
    return found[0]

def get_existing_pid(process_name):
    try:
        output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}" /FO CSV /NH', shell=True).decode()
        if process_name in output:
            parts = output.strip().split(',')
            if len(parts) > 1:
                return int(parts[1].strip('"'))
    except:
        pass
    return None

def main():
    exe_name = "PowerToys.ColorPickerUI.exe"
    event_name = "Local\\ShowColorPickerEvent-8c46be2a-3e05-4186-b56b-4ae986ef2525"
    
    pid = get_existing_pid(exe_name)
    if not pid:
        if not os.path.exists(exe_name):
            print(f"Error: {exe_name} not found.")
            sys.exit(1)
        try:
            subprocess.Popen([exe_name], creationflags=0x08000000)
            time.sleep(1)
            pid = get_existing_pid(exe_name)
            if not pid:
                print("Failed to start or find process.")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to start process: {e}")
            sys.exit(1)

    time.sleep(0.5)
    SYNCHRONIZE = 0x00100000
    EVENT_MODIFY_STATE = 0x0002
    h_event = Kernel32.OpenEventW(EVENT_MODIFY_STATE | SYNCHRONIZE, False, event_name)
    if h_event:
        Kernel32.SetEvent(h_event)
        Kernel32.CloseHandle(h_event)
    
    wrapper_active = False
    
    def is_process_alive(target_pid):
        PROCESS_QUERY_INFORMATION = 0x0400
        h_process = Kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, target_pid)
        if h_process:
            exit_code = ctypes.c_uint()
            Kernel32.GetExitCodeProcess(h_process, ctypes.byref(exit_code))
            Kernel32.CloseHandle(h_process)
            return exit_code.value == 259
        return False

    while True:
        if not is_process_alive(pid):
            if wrapper_active: print("HwndWrapper closed")
            break
        
        current_wrapper_state = is_wrapper_active(pid)
        
        if current_wrapper_state and not wrapper_active:
            wrapper_active = True
            print("HwndWrapper opened")
        elif not current_wrapper_state and wrapper_active:
            wrapper_active = False
            print("HwndWrapper closed")
            
            PROCESS_TERMINATE = 0x0001
            h_process = Kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if h_process:
                Kernel32.TerminateProcess(h_process, 0)
                Kernel32.CloseHandle(h_process)
            break
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()

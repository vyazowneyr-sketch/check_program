import time
import os
import psutil
import io
import sys 
import eel

eel.init('web')
@eel.expose
def run_code(user_code):
    result = execute_code(user_code)
    return result
eel.start('index.html', size=(800, 600))


class TrackerTime:
    def __init__(self, time_name):
        self.time_name = time_name
        self.elapsed = None
        self.message = None  # добавим для сообщения
    
    def __enter__(self):
        self.start_time = time.perf_counter() 
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        
        if exc_type:
            self.message = f" {self.time_name} завершилась с ошибкой: {exc_val.__class__.__name__}: {exc_val}\n    Время до ошибки: {self.elapsed:.3f} сек."
        else:
            self.message = f" {self.time_name} успешно выполнена за {self.elapsed:.3f} сек."
        
        return False


class TrackerMemory:
    def __init__(self, memory_name):
        self.memory_name = memory_name
        self.memory_used = None
        self.message = None  # добавим для сообщения
    
    def __enter__(self):
        self.process = psutil.Process(os.getpid())
        start_memory_bytes = self.process.memory_info().rss
        self.start_memory_mb = start_memory_bytes / (1024 * 1024)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stop_memory_bytes = self.process.memory_info().rss
        stop_memory_mb = stop_memory_bytes / (1024 * 1024)
        self.memory_used = stop_memory_mb - self.start_memory_mb
        
        if exc_type:
            self.message = f"[!] {self.memory_name} завершилась с ошибкой: {exc_val.__class__.__name__}: {exc_val}\n    Использовано памяти до ошибки: {self.memory_used:.2f} МБ"
        else:
            self.message = f"[✓] {self.memory_name} использовала {self.memory_used:.2f} МБ"
        
        return False

def execute_code(user_code: str) -> dict:
    result = {
        "output": None, 
        "error": None,
        "time": None,
        "memory": None,
        "time_message": None, 
        "memory_message": None
    }

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    timer = None
    memory = None

    try:
        with TrackerTime("UserCode") as timer:
            with TrackerMemory("UserCode") as memory:
                namespace = {
                    "__builtins__": __builtins__,
                }
                import math, random, json
                namespace.update({
                    "math": math,
                    "random": random,
                    "json": json,
                })
                
                exec(user_code, namespace)
                
                if "_result" in namespace:
                    result["output"] = str(namespace["_result"])
        
        result["output"] = buffer.getvalue().strip()
        result["time"] = timer.elapsed
        result["memory"] = memory.memory_used
        result["time_message"] = timer.message
        result["memory_message"] = memory.message

    except Exception as e:
        result["output"] = buffer.getvalue()
        result["error"] = str(e)
        if timer:
            result["time"] = timer.elapsed
        if memory:
            result["memory"] = memory.memory_used

    finally:
        sys.stdout = old_stdout

    return result


result = execute_code("print('Привет!'); x = 5 * 10")
print(result)

result = execute_code("import math; print(math.pi)")
print(result)

result = execute_code("print('Start'); raise ValueError('Ошибка!')")
print(result)
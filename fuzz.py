import os
import random
import string
import tempfile
import traceback

import pandas as pd
import importlib.util

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)



LOGFILE = "fuzz_results.txt"


def log(msg: str) -> None:
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def load_module_from_rel_path(module_name: str, relative_path: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {module_name} from {full_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_function_from_file(relative_path, func_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, relative_path)
    safe_lines = []
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            if "from git" in line or "import git" in line:
                continue
            if "import subprocess" in line:
                continue
            if "import shutil" in line:
                continue
            safe_lines.append(line)
    code = "".join(safe_lines)
    temp_mod = {"__builtins__": __builtins__}
    exec(code, temp_mod)
    if func_name not in temp_mod:
        raise ImportError(f"Function {func_name} not found in sanitized {relative_path}")
    return temp_mod[func_name]


frequency_mod = load_module_from_rel_path(
    "frequency",
    os.path.join("MLForensics-farzana", "empirical", "frequency.py"),
)

report_mod = load_module_from_rel_path(
    "report",
    os.path.join("MLForensics-farzana", "empirical", "report.py"),
)

getAllSLOC = frequency_mod.getAllSLOC
giveTimeStamp = frequency_mod.giveTimeStamp

Average = report_mod.Average
Median = report_mod.Median

makeChunks = load_function_from_file(
    os.path.join("MLForensics-farzana", "mining", "mining.py"),
    "makeChunks",
)

dumpContentIntoFile = load_function_from_file(
    os.path.join("MLForensics-farzana", "mining", "mining.py"),
    "dumpContentIntoFile",
)


def random_string(length: int = 20) -> str:
    chars = string.ascii_letters + string.digits + " "
    return "".join(random.choice(chars) for _ in range(length))


def fuzz_getAllSLOC() -> None:
    tmp_files = []
    try:
        num_files = random.randint(1, 5)
        paths = []
        for _ in range(num_files):
            fd, path = tempfile.mkstemp()
            tmp_files.append(path)
            with os.fdopen(fd, "w", encoding="latin-1") as f:
                for _ in range(random.randint(1, 30)):
                    f.write(random_string(random.randint(5, 40)) + "\n")
            paths.append(path)
        df = pd.DataFrame({"FILE_FULL_PATH": paths})
        result = getAllSLOC(df)
        log(f"[OK] getAllSLOC -> total_sloc={result} for {num_files} files")
    except Exception:
        log("[ERROR] getAllSLOC crashed:\n" + traceback.format_exc())
    finally:
        for path in tmp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def fuzz_Average() -> None:
    try:
        size = random.randint(1, 25)
        lst = [random.uniform(-1_000, 1_000) for _ in range(size)]
        result = Average(lst)
        log(f"[OK] Average -> input_len={len(lst)}, result={result}")
    except Exception:
        log("[ERROR] Average crashed:\n" + traceback.format_exc())


def fuzz_Median() -> None:
    try:
        size = random.randint(1, 25)
        lst = [random.uniform(-1_000, 1_000) for _ in range(size)]
        result = Median(lst)
        log(f"[OK] Median -> input_len={len(lst)}, result={result}")
    except Exception:
        log("[ERROR] Median crashed:\n" + traceback.format_exc())


def fuzz_makeChunks() -> None:
    try:
        list_size = random.randint(0, 40)
        lst = [random.randint(-1000, 1000) for _ in range(list_size)]
        size_ = random.randint(1, 10)
        chunks = list(makeChunks(lst, size_))
        log(
            f"[OK] makeChunks -> list_size={len(lst)}, chunk_size={size_}, "
            f"num_chunks={len(chunks)}"
        )
    except Exception:
        log("[ERROR] makeChunks crashed:\n" + traceback.format_exc())


def fuzz_dumpContentIntoFile() -> None:
    temp_path = None
    try:
        content = random_string(random.randint(0, 200))
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        result = dumpContentIntoFile(content, temp_path)
        log(
            f"[OK] dumpContentIntoFile -> content_len={len(content)}, "
            f"reported_size={result}"
        )
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        log("[ERROR] dumpContentIntoFile crashed:\n" + traceback.format_exc())
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def main() -> None:
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    try:
        ts = giveTimeStamp()
    except Exception:
        ts = "UNKNOWN_TIMESTAMP"
    log("------ FUZZING START ------")
    log(f"Timestamp: {ts}")
    rounds = 50
    for i in range(rounds):
        log(f"[ROUND {i+1}/{rounds}]")
        fuzz_getAllSLOC()
        fuzz_Average()
        fuzz_Median()
        fuzz_makeChunks()
        fuzz_dumpContentIntoFile()
    log("------ FUZZING END ------")


if __name__ == "__main__":
    main()

from pathlib import Path
import platform


PATH_BASE = Path(__file__).resolve().parent


def files_check(files: list) -> dict:
    output_check = {
        'done': [],
        'error': []
    }

    for file in files:
        direct = Path(file)
        if direct.exists():
            output_check['done'].append(file)
        else:
            output_check['error'].append(file)

    return output_check


def disable_progress_bar(inc_bar):
    def nothing():
        pass
    inc_bar.start = nothing
    inc_bar.next = nothing
    inc_bar.finish = nothing

    return inc_bar


def get_system_info() -> tuple[str, str]:
    system = platform.system()
    bit_info = platform.machine()

    if system == "Linux":
        if bit_info not in ['x86_64', 'aarch64']:
            raise OSError(f"{bit_info} doesn't support")
    else:
        raise OSError(f"{system} doesn't support")

    return system, bit_info

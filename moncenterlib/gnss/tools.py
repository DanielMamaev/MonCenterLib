from pathlib import Path


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

from pathlib import Path


def type_check(*types):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Проверка типов аргументов
            for i, arg in enumerate(args[1:]):
                if not isinstance(arg, types[i][0]):
                    raise TypeError(f"The type of the '{types[i][1]}' variable should be {types[i][0].__name__}")
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


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

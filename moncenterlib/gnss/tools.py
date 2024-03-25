from pathlib import Path


def get_start_date_from_nav(file_nav: str) -> str:
    date_nav: list[str] = []
    with open(file_nav, 'r', encoding="utf-8") as f_nav:
        data = f_nav.readlines()
        for i, line in enumerate(data):
            if 'RINEX VERSION' in line:
                rinex_v = line.split()[0]
                if not (rinex_v.startswith("2") or rinex_v.startswith("3")):
                    raise Exception(f"Unknown version rinex {rinex_v}")

            if 'END OF HEADER' in line:
                date_nav = data[i + 1].split()[1:4]

                if len(date_nav[0]) == 2:
                    # for rinex v1,2
                    if 80 <= int(date_nav[0]) <= 99:
                        date_nav[0] = "19" + date_nav[0]
                    # for rinex v3
                    elif 0 <= int(date_nav[0]) <= 79:
                        date_nav[0] = "20" + date_nav[0]

                date_nav[1] = date_nav[1].zfill(2)
                date_nav[2] = date_nav[2].zfill(2)
                break
    return "-".join(date_nav)


def get_start_date_from_obs(file_obs: str) -> str:
    date_obs = ""
    with open(file_obs, 'r', encoding="utf-8") as f_obs:
        for line_obs in f_obs:
            if 'RINEX VERSION' in line_obs:
                rinex_v = line_obs.split()[0]
                if not (rinex_v.startswith("2") or rinex_v.startswith("3")):
                    raise Exception(f"Unknown version rinex {rinex_v}")

            if 'TIME OF FIRST OBS' in line_obs:
                date_obs = line_obs.split()[:3]
                date_obs[1] = date_obs[1].zfill(2)
                date_obs[2] = date_obs[2].zfill(2)
                date_obs = '-'.join(date_obs)
    return date_obs


def get_marker_name(file: str) -> str:
    marker_name = ""
    with open(file, 'r', encoding="utf-8") as f:
        for line_obs in f:
            if 'RINEX VERSION' in line_obs:
                rinex_v = line_obs.split()[0]
                if not (rinex_v.startswith("2") or rinex_v.startswith("3")):
                    raise Exception(f"Unknown version rinex {rinex_v}")

            if 'MARKER NAME' in line_obs:
                marker_name = line_obs.split()[0]
                if marker_name == "MARKER":
                    marker_name = Path(file).name
    return marker_name

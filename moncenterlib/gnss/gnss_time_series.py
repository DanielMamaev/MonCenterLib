from collections import defaultdict
from typeguard import typechecked


@typechecked
def parse_pos_file(path2file: str, sep: str | None = None) -> tuple[dict[str, list], list[list[str]]]:
    """This function for parsing .pos file. The method returns header, name of columns and time serie.

    Args:
        path2file (str): Path to the file .pos
        sep (str | None, optional): If .pos file has separation (e.g. ;) use sep=";". Defaults to None.

    Returns:
        tuple[dict[str, list], list[list[str]]]: Return tuple. First item is header of .pos file.
            Second item is time serie.
    """

    header = defaultdict(list)
    data = list()

    with open(path2file, 'r', encoding="utf-8") as f:
        for line in f:
            # parse header
            if line.startswith("%") and ": " in line:
                info = line.split(": ")
                key = info[0].replace("% ", "").strip()
                value = info[1].replace("\n", "").strip()
                header[key] += [value]

            # parse name columns
            elif line.startswith("%") and "ratio" in line:
                name_columns = line.split()[1:]
                header["name_columns"] = name_columns

            # parse data
            elif not line.startswith("%"):
                row = line.split(sep)
                # concatenation time
                row[1] = f"{row[0]} {row[1]}"
                row.pop(0)

                if "latitude(d\'\")" in header["name_columns"]:  # llh and dms
                    row[1] = ' '.join(row[1:4])  # date d m s
                    row.pop(2)  # date dms m
                    row.pop(2)  # date dms
                    row[2] = ' '.join(row[2:5])  # date dms d m s
                    row.pop(3)  # date dms dms m
                    row.pop(3)  # date dms dms
                else:
                    row[1] = float(row[1]) # coord 1
                    row[2] = float(row[2]) # coord 2
                
                row[3] = float(row[3]) # coord 3
                row[4] = int(row[4]) # Q
                row[5] = int(row[5]) # ns
                
                row[6] = int(row[6]) # sd coord 1
                row[7] = int(row[7]) # sd coord 2
                row[8] = int(row[8]) # sd coord 3
                row[9] = int(row[9]) # sd coord 1 2
                row[10] = int(row[10]) # sd coord 2 3
                row[11] = int(row[11]) # sd coord 1 3
                row[12] = int(row[12]) # age
                row[13] = int(row[13]) # ratio 

                data.append(row)

    return dict(header), data

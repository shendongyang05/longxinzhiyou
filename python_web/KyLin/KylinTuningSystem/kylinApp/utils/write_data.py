import csv


def data_processing(data) -> list:
    data = [[]]
    return data


def open_file_write(file_path, title, data):
    with open(file_path , mode="w" , newline='') as file:
        writer = csv.writer(file)
        writer.writerow(title)
        writer.writerows(data_processing(data))


def open_file_read(file_path):
    with open(file_path , mode="r" , newline='') as file:
        return file.read()


def write_data(data, tp):
    biotop_title = ["PID", "COMM", "D", "MAJ", "MIN", "DISK", "I/O", "Kbytes", "AVGms"]
    xfsslower_title = ["TIME", "COMM", "PID", "T", "BYTES", r"OFF\_KB", "LAT(ms)", "FILENAME"]

    for tp_name in tp:
        if tp_name == "biotop":
            open_file_write("biotop_data.csv", biotop_title, data)
        elif tp_name == "xfsslower":
            open_file_write("xfsslower_data.csv", xfsslower_title, data)


def read_data(file_path=None):
    if file_path is None:
        file_path = ["biotop_data.csv", "xfsslower_data.csv"]
        file_data = []
        for item in file_path:
            data = open_file_read(item)
            file_data.append(data)
        return file_data

import crawler
import json
import time
import datetime
import sys
import os
import zlib
from itertools import groupby

EXTENSION = ".json.zz"


def read_file(filename):
    with open(filename, "rb") as f:
        binary = zlib.decompress(f.read())
        return json.loads(binary.decode("utf-8"))


def write_file(filename, obj):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        binary = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        f.write(zlib.compress(binary))


def archive(output_dir, temp_dir):
    current_date = datetime.datetime.utcnow().date()
    if os.path.isdir(temp_dir):
        files = [
            os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
            if f.endswith(EXTENSION)
        ]
        for file_date, _ in groupby(files, lambda f: datetime.datetime.utcfromtimestamp(int(os.path.basename(f).split('.')[0])).date()):
            files_of_date = list(_)
            if file_date < current_date:
                archive_filename = os.path.join(
                    output_dir,
                    file_date.strftime("%Y"),
                    file_date.strftime("%m"),
                    file_date.strftime("%d") + EXTENSION,
                )
                if os.path.isfile(archive_filename):
                    data = read_file(archive_filename)
                else:
                    data = []
                for _ in sorted(files_of_date):
                    data.append(read_file(_))
                write_file(archive_filename, data)
                print(
                    f"Archive of date {file_date} is written to {archive_filename}"
                )
                for _ in files_of_date:
                    os.remove(_)
                    print(f"Deleted file {_}")


def crawl(temp_dir, error_dir):
    timestamp = int(time.time())
    body = None
    hotwords = None
    error = None

    try:
        body = crawler.fetch()
        hotwords = crawler.extract(body)
    except Exception as e:
        error = str(e)

    output = {
        "timestamp": timestamp,
    }
    if error:
        output["error"] = error
        output["http_body"] = body
    else:
        output["hotwords"] = hotwords

    result_filename = os.path.join(error_dir if error else temp_dir,
                                   f"{timestamp}{EXTENSION}")
    write_file(result_filename, output)
    print(f"Crawl result is written to {result_filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "."
    output_dir = os.path.abspath(output_dir)
    temp_dir = os.path.join(output_dir, "temp")
    error_dir = os.path.join(output_dir, "error")

    archive(output_dir, temp_dir)
    crawl(temp_dir, error_dir)

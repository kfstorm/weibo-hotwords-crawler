import crawler
import json
import time
import datetime
import sys
import os
from itertools import groupby


def read_json_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(filename, obj):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def archive(output_dir, temp_dir):
    current_date = datetime.datetime.utcnow().date()
    if os.path.isdir(temp_dir):
        files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".json")]
        for file_date, _ in groupby(files, lambda f: datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(f))[0])).date()):
            files_of_date = list(_)
            if file_date < current_date:
                archive_filename = os.path.join(
                    output_dir,
                    file_date.strftime("%Y"),
                    file_date.strftime("%m"),
                    file_date.strftime("%d") + ".json",
                )
                if os.path.isfile(archive_filename):
                    data = read_json_file(archive_filename)
                else:
                    data = []
                for _ in sorted(files_of_date):
                    data.append(read_json_file(_))
                write_json_file(archive_filename, data)
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

    result_filename = os.path.join(error_dir
                                   if error else temp_dir, f"{timestamp}.json")
    write_json_file(result_filename, output)
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

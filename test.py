import requests
import gzip
from io import BytesIO

url = "https://misis-admission.seizure.icu/btns/1.0"

headers = {
    "Accept-Encoding": "gzip"
}

response = requests.get(url, headers=headers)

if response.headers.get("Content-Encoding") == "gzip":
    compressed_data = BytesIO(response.content)
    decompressed_data = gzip.GzipFile(fileobj=compressed_data).read()
    print(decompressed_data.decode("utf-8"))
else:
    print(response.text)

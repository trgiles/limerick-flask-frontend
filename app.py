from flask import Flask
import boto3
from collections import defaultdict
import json

#try from staging...idk
#This is another test from staging...we will see...

app = Flask(__name__)

s3 = boto3.client("s3")

BUCKET_NAME = "limerick-photo-bucket"

def generate_url(key):
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key
        },
        ExpiresIn=3600 # 1 hour
    )

@app.route("/")
def home():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)

    if "Contents" not in response:
        return "<h1>No batches found</h1>"

    batches = defaultdict(list)

    for obj in response["Contents"]:
        key = obj["Key"]

        if "/" not in key:
            continue # skip root-level junk if any

        batch = key.split("/")[0]
        batches[batch].append(key)

    html = "<h1>Batches (this is a test...)</h1><p>and it is pretty awesome!</p><ul>"

    for batch in sorted(batches.keys(), reverse=True):
        html += f'<li><a href="/batch/{batch}">{batch}</a></li>'

    html += "</ul>"

    return html

@app.route("/batch/<batch_id>")
def view_batch(batch_id):
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=f"{batch_id}/"
    )

    if "Contents" not in response:
        return "<h1>No images found</h1>"

    images = []
    caption = ""

    for obj in response["Contents"]:
        key = obj["Key"]

        if key.lower().endswith("result.json"):
            result = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            body = result["Body"].read().decode("utf-8")

            data = json.loads(body)

            #caption = data["output"][0]["content"][0]["text"]
            try:
                caption = (
                    data.get("output", [{}])[0] #some result jsons need index 1...
                        .get("content", [{}])[0]
                        .get("text", "")
                )
            except Exception as e:
                print(f"ERROR: {e}")

        if key.endswith("/") or key.lower().endswith(".json"):
            continue

        images.append(key)

    html = f"<h1>Batch: {batch_id}</h1>"

    html += """
<style>
    .gallery-caption {
        max-width: 800px;
	margin: 40px auto 0 auto;
	padding: 20px 24px;
	background: #1a1a1a;
	border-radius: 12px;
	color: #d6d6d6;
	line-height: 1.6;
	font-size: 15px;
	box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    }
    .gallery-caption p {
	margin: 0;
	font-size: 16px;
	letter-spacing: 0.2px;
    }
    .grid{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 10px;
    }
    img {
        width: 100%;
        height: auto;
        border-radius: 8px;
    }
</style>
<div class="grid">
"""

    for img_key in images:
        url = generate_url(img_key)
        html += f'<img src="{url}">'

    html += "</div>"

    if caption: html += f'<div class="gallery-caption"><p>{caption}</p></div>'

    return html




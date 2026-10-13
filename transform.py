import os
import sys
import json
import time
import shutil
import argparse
import traceback
import requests
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
API_KEY = os.environ.get("EI_PROJECT_API_KEY")
INGESTION_HOST = os.environ.get("EI_INGESTION_HOST", "edgeimpulse.com")

if not GEMINI_API_KEY:
    print("Missing GEMINI_API_KEY")
    sys.exit(1)
if not API_KEY:
    print("Missing EI_PROJECT_API_KEY")
    sys.exit(1)

parser = argparse.ArgumentParser(description="Generate images with Gemini and upload them to Edge Impulse")
parser.add_argument("--prompt", type=str, required=True)
parser.add_argument("--label", type=str, required=True)
parser.add_argument("--images", type=int, required=True)
parser.add_argument("--model", type=str, default="gemini-3.1-flash-image")
parser.add_argument("--aspect-ratio", "--aspect_ratio", dest="aspect_ratio", type=str, default="1:1")
parser.add_argument("--upload-category", "--upload_category", dest="upload_category", type=str, default="split")
parser.add_argument("--synthetic-data-job-id", type=int, required=False)
parser.add_argument("--skip-upload", action="store_true")
parser.add_argument("--out-directory", type=str, default="output")
args, _unknown = parser.parse_known_args()

INGESTION_URL = f"https://ingestion.{INGESTION_HOST}"
if INGESTION_HOST.endswith(".test.edgeimpulse.com"):
    INGESTION_URL = f"http://ingestion.{INGESTION_HOST}"
if INGESTION_HOST == "host.docker.internal":
    INGESTION_URL = f"http://{INGESTION_HOST}:4810"

if os.path.exists(args.out_directory):
    shutil.rmtree(args.out_directory)
os.makedirs(args.out_directory)

client = genai.Client(api_key=GEMINI_API_KEY)
epoch = int(time.time())

# Small wording variations so the images are not all near-identical
VARIATIONS = [
    "", "Slightly different camera angle.", "Different lighting.", "Different background.",
    "Closer framing.", "Wider framing.", "Different time of day.", "Different object placement.",
]

def generate_image(prompt):
    try:
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=args.aspect_ratio),
        )
    except Exception:
        config = types.GenerateContentConfig(response_modalities=["IMAGE"])

    response = client.models.generate_content(model=args.model, contents=prompt, config=config)

    for cand in (response.candidates or []):
        for part in (cand.content.parts or []):
            if getattr(part, "inline_data", None) and part.inline_data.data:
                mime = part.inline_data.mime_type or "image/png"
                return part.inline_data.data, mime
    raise Exception("Gemini returned no image (possibly blocked by safety filters). Text: "
                    + str(getattr(response, "text", "")))

print("Prompt:", args.prompt)
print("Model:", args.model)
print("Number of images:", args.images)
print("")

MAX_RETRIES = 3
MAX_DELAY = 60

for i in range(args.images):
    prompt = (args.prompt + " " + VARIATIONS[i % len(VARIATIONS)]).strip()
    print(f"Creating image {i + 1} of {args.images} for {args.label}...", end="", flush=True)

    retries = 0
    success = False
    while retries < MAX_RETRIES and not success:
        try:
            image_bytes, mime = generate_image(prompt)
            ext = "jpg" if "jpeg" in mime else "png"
            filename = f"{args.label}.{epoch}.{i}.{ext}"
            with open(os.path.join(args.out_directory, filename), "wb") as f:
                f.write(image_bytes)

            if not args.skip_upload:
                headers = {
                    "x-label": args.label,
                    "x-api-key": API_KEY,
                    "x-metadata": json.dumps({"generated_by": "gemini", "model": args.model, "prompt": prompt}),
                }
                if args.synthetic_data_job_id is not None:
                    headers["x-synthetic-data-job-id"] = str(args.synthetic_data_job_id)

                res = requests.post(
                    url=f"{INGESTION_URL}/api/{args.upload_category}/files",
                    headers=headers,
                    files={"data": (filename, image_bytes, mime)},
                )
                if res.status_code != 200:
                    raise Exception(f"Upload failed ({res.status_code}): {res.content.decode('utf-8')}")
                body = json.loads(res.content.decode("utf-8"))
                if not body["success"]:
                    raise Exception(f"Upload failed: {body['error']}")
                if not body["files"][0]["success"]:
                    raise Exception(f"Upload failed: {body['files'][0]['error']}")

            print(" OK")
            success = True
        except Exception as e:
            retries += 1
            print(f"\nAttempt {retries} failed for image {i + 1}: {e}")
            print(traceback.format_exc())
            if retries < MAX_RETRIES:
                delay = min(3 ** retries, MAX_DELAY)
                print(f"Waiting {delay}s before retrying...")
                time.sleep(delay)
            else:
                print(f"Giving up on image {i + 1}.")

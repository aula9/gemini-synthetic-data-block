# Gemini Synthetic Data Block for Edge Impulse

A custom [synthetic data block](https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-synthetic-data-blocks)
that generates images with Google Gemini and uploads them directly to an
Edge Impulse project with a label.
![Gemini synthetic data block ](gemini-block-mascot.svg)

## What it does

1. Takes a text prompt (e.g. "a realistic photo of a pizza slice on a wooden table").
2. Generates N images with a Gemini image model.
3. Uploads them to your project with the label and train/test category you choose.

To avoid near-identical images, the block appends small wording variations to the
prompt (different angle, lighting, background, framing...). Failed generations are
retried up to 3 times, and each image is uploaded with metadata (model and prompt).

## Parameters

| Parameter | Description |
|---|---|
| **Gemini API Key** | Key from [Google AI Studio](https://aistudio.google.com/apikey) (stored as a secret) |
| **Prompt** | Text prompt describing the images |
| **Label** | Label assigned to the uploaded images |
| **Number of images** | How many images to generate |
| **Upload to category** | Split 80/20, Training, or Testing |
| **Gemini model** | Image model name (default: `gemini-3.1-flash-image`) |
| **Aspect Ratio** | e.g. `1:1`, `4:3`, `16:9` |

## Using the block in Studio

1. Open your project, then **Data acquisition → Synthetic data**.
2. Select this block from the list of synthetic data sources.
3. Enter your Gemini API key, prompt, label and number of images.
4. Run the job and check the new images in the **Dataset** tab.

## Publishing the block to your organization

Requires Node.js, the Edge Impulse CLI and an Enterprise organization.
See the [official CLI installation guide](https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/installation)
for the install command for your system, then:

    edge-impulse-blocks init
    edge-impulse-blocks push

Windows note: on Windows 10 the CLI install failed for me with a `sharp`
download timeout. I worked around it by running `npm install -g edge-impulse-cli --ignore-scripts` to skip the problematic binary download. After confirming that `C:\Users\User\AppData\Roaming\npm` was added to the system PATH, the `edge-impulse-blocks` command worked successfully (note: the executable is `edge-impulse-blocks`, not `edge-impulse-cli`).

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Container definition (Python 3.11) |
| `transform.py` | Generates images with Gemini and uploads them |
| `parameters.json` | Parameters shown in the Studio UI |
| `requirements.txt` | Python dependencies (`google-genai`, `requests`) |

## Notes

- Never commit your API key. Enter it only as a secret in the Studio UI.
- Gemini may refuse some prompts because of safety filters; the job log shows the reason.
- Always review generated images before training. Synthetic images can contain
  visual errors or look unrealistic compared with real camera data.
- Model names and availability change. If a model name fails, check Google AI Studio
  for the current image model names.

## Credits

Structure based on Edge Impulse's example synthetic data block
(example-transform-Astra-images).

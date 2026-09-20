# Generative AI Assignment — Part 1 Instructions

[Assignment workspace](../../../assignments/generative-ai/README.md)

Formatted version of the instructor's instructions. The original steps, commands, filenames, and links are retained. Paths below refer to the instructor's package.

Current project transcripts are kept once in [the canonical Obsidian corpus](../../../assignments/generative-ai/notes/Transcripts/). Package paths in the historical instructions below are not duplicate storage locations. Use the [current Part 1 scripts](../../../assignments/generative-ai/part1/README.md) for preparation.

## Contents

1. [Install the Python environment](#step-1-install-the-python-environment)
2. [Open the notebook and select the channel](#step-2-open-the-notebook-and-select-the-channel)
3. [Keep the computer awake](#step-3-keep-the-computer-awake)
4. [Download the transcripts](#step-4-download-the-transcripts)
5. [Combine transcripts, map titles, and extract themes](#step-5-combine-transcripts-map-titles-and-extract-themes)
6. [Rename the transcripts](#step-6-rename-the-transcripts)
7. [Prepare DeepSeek for Part 2](#step-7-prepare-deepseek-for-part-2)

## Step 1: Install the Python environment

1. Install **Anaconda**.
2. Put `Youtube_AI_students\deepseek_api.yml` within your root directory, for example `C:\Users\YourUserName` on Windows, or the corresponding directory on Mac.
3. Open the Anaconda prompt, which will open in `C:\Users\YourUser`, or the corresponding terminal on Mac.
4. Run:

   ```bash
   conda env create -f deepseek_api.yml
   ```

This creates the `deepseek_api` environment with all packages listed in the YAML file.

**On Mac, use `deepseek_api_mac.yml`.**

## Step 2: Open the notebook and select the channel

Open the Anaconda prompt, or the corresponding terminal on Mac, and run:

```text
activate deepseek_api
jupyter notebook
```

When Jupyter Notebook opens, browse to and open:

```text
Youtube_AI_students\1.youtube_transcripts_YYYYMMDD_identifier.ipynb
```

Go to line 37:

```python
CHANNEL_HANDLE = "@FelixFriends"
```

Change the channel handle to **`@HeresyFinancial`**.

The channels listed in the instructions are:

| Channel | Description |
|---|---|
| `@HeresyFinancial` | Economics and finance educator |
| `@RebelCapitalistChannel` | Economics and finance educator |
| `@allthingsfinancial0` | Macroeconomics and finance educator |
| `@FelixFriends` | Economics and finance educator |
| `@benjaminjcowen` | Crypto finance |
| `@TheCryptoverse` | Crypto finance |

## Step 3: Keep the computer awake

At night, before you go to bed:

1. Go to **Power & sleep settings** in Windows, or the corresponding interactive window on Mac.
2. Set the computer to **never sleep**.

## Step 4: Download the transcripts

### Run the download notebook

At night, before you go to bed, run:

```text
Youtube_AI_students\1.youtube_transcripts_YYYYMMDD_identifier.ipynb
```

Run it for the whole night.

It will slowly download video transcripts from the channel and put them in:

```text
Youtube_AI\transcripts_ids
```

Each transcript will be a text file named:

```text
YYYYMMDD_VIDEOID.md
```

The directory `transcripts_upto_20260514` contains video transcripts up to **2026-05-14**. The notebook downloads transcripts starting from the most recent one.

**Download enough video transcripts to cover the gap from 2026-05-14 to now.**

To see what has been downloaded, organize the text files in alphabetical order. This also organizes them by date.

The instructions estimate that this many transcripts will take about **three or four nights**.

### Check for throttling

The instructions state that throttling should not happen outside UofT, but may happen when using a UofT IP address.

Before going to bed:

1. Run `Youtube_AI_students\1.youtube_transcripts_YYYYMMDD_identifier.ipynb` for half an hour.
2. Look at the printed output.
3. Make sure YouTube is not throttling the downloads.

If errors occur because YouTube throttles the downloads:

1. Download and install [free Proton VPN](https://protonvpn.com/download?srsltid=AfmBOorM5E65EfhsGsbhMH1V-8ZLCxCPmRHiqnDkQWlHi68Sgpah4HQq).
2. Run Proton VPN to change the UofT IP to a Proton VPN IP.
3. Rerun the download notebook.
4. If YouTube still throttles the downloads, go to the notebook's **CONFIG** section and change `MAX_PER_RUN = 4` to **3 or 2**.

## Step 5: Combine transcripts, map titles, and extract themes

### Combine the old and new transcripts

After downloading the video transcripts, put the contents of:

```text
Youtube_AI_students\transcripts_ids_upto_20260514
```

into:

```text
Youtube_AI_students\transcripts_ids
```

This unifies the old and new transcripts.

### Run the title mapper

Run:

```text
Youtube_AI_students\2.youtube_id_title_date_mapper.py
```

To run it:

1. Open the Anaconda prompt, which will open in `C:\Users\YourUser`, or the corresponding terminal on Mac.
2. Run:

   ```text
   activate deepseek_api
   Spyder
   ```

3. When Spyder opens, browse to `Youtube_AI_students\2.youtube_id_title_date_mapper.py` and run the script.

The script outputs:

```text
Youtube_AI_students\youtube_channel_videos.csv
```

This file contains a mapping from `video_id` to `video_title`.

### Extract a detailed list of themes

1. Upload `youtube_channel_videos.csv` to Claude or ChatGPT, preferably the free version.
2. Ask it to use the **`video_title` column** to extract a detailed list of themes.
3. **Save the results.**

## Step 6: Rename the transcripts

After creating `youtube_channel_videos.csv`, run:

```text
Youtube_AI_students\3.rename_transcripts.py
```

This creates a new directory:

```text
Youtube_AI_students\transcripts
```

The video transcripts will be saved with filenames in this format:

```text
YYYYMMDD_VIDEOTITLE.md
```

## Step 7: Prepare DeepSeek for Part 2

Set up an API key for the [DeepSeek LLM](https://www.deepseek.com/) and pay **CAD 12–15** into the account. The instructions note that more transcripts require more money.

You will use this for **Part 2** of the project.

## What comes next

The downloaded transcripts will be used in the next steps to learn how to instruct Claude or ChatGPT, preferably the free version, to program a Python workflow that uses another LLM, DeepSeek.

The workflow will construct a knowledge base in a Markdown file, using the following epistemic hierarchy to synthesize the many hundreds of transcripts from the selected crypto-finance YouTube channel:

```text
Claim → Theme → Argument → Evidence & EvolutionOverTime
```

The instructor states the purpose of the knowledge base as follows:

> Given the knowledge base, any LLM can provide detailed answers about the contents of the chosen crypto finance YouTube channel without hallucinating.

The instructions conclude:

> You will NOT have to program a single line of Python.
>
> We will teach you how to write the prompt for Claude, and how to write prompts in general.

import os
import glob
import re

def convert_time_to_srt(time_seconds):
    hours, remainder = divmod(time_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = (seconds % 1) * 1000
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"

def txt_to_srt(input_folder):
    text_pattern = re.compile(r"(\d+\.\d+|\d+)_(\d+)\.txt$")
    srt_entries = []

    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    for txt_file in txt_files:
        basename = os.path.basename(txt_file)
        match = text_pattern.match(basename)
        if match:
            start_time, index = match.groups()
            start_time_srt = convert_time_to_srt(float(start_time))
            
            # Assuming a default duration of 5 seconds for each subtitle
            end_time_srt = convert_time_to_srt(float(start_time) + 5)
            
            with open(txt_file, 'r', encoding='utf-8') as file:
                content = file.read().strip()
            
            srt_entry = f"{index}\n{start_time_srt} --> {end_time_srt}\n{content}\n"
            srt_entries.append((int(index), srt_entry))
    
    # Sort entries by index to ensure the correct order
    srt_entries.sort(key=lambda x: x[0])
    
    # Write to a single SRT file
    output_file = os.path.join(input_folder, "output.srt")
    with open(output_file, 'w', encoding='utf-8') as file:
        for _, entry in srt_entries:
            file.write(entry + "\n")

# Specify the input folder path
input_folder = "path/to/your/txt/files"
txt_to_srt(input_folder)

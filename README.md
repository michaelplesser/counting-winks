# counting-winks
One night, on a very safe stroll around Mission Hill in Boston, I noticed two lights blinking in phase on the downtown skyline. Pleasing though it was, over the course of 5-10 minutes the lights drifted out of phase slowly. Curious as to how long the beat period was between the two lights, I took a video and wrote this program to analyze the frequency information using fourier transforms.

## Dependency installation:
The code uses several common libraries, but if not installed they can be obtained with pip3.
```
pip3 install scipy
pip3 install matplotlib
pip3 install numpy
```
### PyAv module
Note: The code to process video is included for reference, but the video file is not included out of convenience. It is a large file and the processing takes a few minutes, so it is easier to just provide the processed data arrays under data/<file_name>.npy. Unless you plan to process a video there's no reason to bother installing PyAv, which has difficult dependencies to resolve. If you do want to install PyAv my advice is make sure you have an up to date version of ffmpeg, and perhaps try conda since pip3 wasn't able to do the installation cleanly for me first try.

## How to run:
Running the code should be very easy. The following should work out-of-box once you've installed all dependencies.
```
git clone https://github.com/michaelplesser/counting-winks.git
cd counting-winks/
python3 counting-winks.py
```
For more help, try
```
python3 counting-winks.py --help
```

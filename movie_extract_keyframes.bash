#!/usr/bin/env bash
if [ -z "$2" -o -e "$2" -a ! -d "$2" ]; then
  echo "Usage: movie-extract-keyframes.bash movie.mp4 output-dir" 1>&2
  exit 1
fi

input="$1"
output="$2"
vf="$3"

mkdir -p "$output"

#sws_flags
#    ‘fast_bilinear’ ‘bilinear’ ‘bicubic’ ‘experimental’ ‘neighbor’
#    ‘area’ ‘bicublin’ ‘gauss’ ‘sinc’ ‘lanczos’ ‘spline’
#    ‘print_info’ ‘accurate_rnd’ ‘full_chroma_int’ ‘full_chroma_inp’ ‘bitexact’

#ffmpeg -i "$input" \
#    -vf select="eq(pict_type\,PICT_TYPE_I)",scale=-1:360:flags="bicublin",crop=640:360 \
#    -vsync 2 \
#    -f image2 \
#    "$output"/%06d.png \
#    -loglevel debug 2>&1

# stdbuf -oL cmd args

# ffmpeg -i "$input" \
#     -sws_flags bicublin \
#     -sws_dither bayer \
#     -q:v 1 \
#     -vf select="eq(pict_type\,PICT_TYPE_I)",scale=-1:480,crop=640:360 \
#     -vsync 2 \
#     -f image2 \
#     "$output"/%06d.png \
#     -loglevel debug 2>&1 \
#     | sed -n -e 's/^.* n:\([0-9.]*\) .* -> select:1\..*/\1/p' \
#     | tee "$output"/timecodes.txt

ffmpeg -i "$input" \
    -sws_flags bicublin \
    -sws_dither bayer \
    -q:v 1 \
    -vf select="eq(pict_type\,PICT_TYPE_I)""$vf" \
    -vsync 2 \
    -f image2 \
    "$output"/%06d.png \
    -loglevel debug 2>&1 \
    | sed -n -e 's/^.* n:\([0-9.]*\) .* -> select:1\..*/\1/p' \
    | tee "$output"/timecodes.txt >/dev/null
            

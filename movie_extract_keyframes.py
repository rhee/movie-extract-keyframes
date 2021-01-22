# coding: utf-8
from traceback import print_exc
import os
import sys
import subprocess
import re
from os.path import isdir, join, splitext

import logging
import threading
if isinstance(threading.current_thread(), threading._MainThread):
    logging.basicConfig(format='%(asctime)s %(levelname)-.1s %(filename)s:%(lineno)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('keyframes')


def movie_extract_keyframes(input_file, output_dir,
                            output_file_type='.png',
                            extract_all_frames=False,
                            rotate=0,
                            width=None,
                            height=None,
                            fps=None,
                            process_encoding=None,
                            verbose=False,
                            timecodehandle=None,
                            max_frames=None,
                            **extra_kwargs):
    """
    time ffmpeg -i "$input" \
        -q:v 1 \
        -vf select="eq(pict_type\,PICT_TYPE_I)$extra_vf" \
        -vsync 2 \
        -f image2 \
        "$output"/%06d.png \
        -loglevel debug 2>&1 \
            | tee "$output"/log.txt \
        | sed -n -e 's/^.* n:\([0-9.]*\) .* -> select:1\..*/\1/p' \
        | tee "$output"/timecodes.txt

    frame name pattern in log output:

    # pattern: [image2 @ 000001b06c8459c0] Opening 'image\000204.jpg' for writing
    # pattern: [image2 @ 0x55d9e4eb19e0] Opening 'sample/7-3.frames//009472.png' for writing

    alternative command:

    ffmpeg_command = [
        'ffmpeg',
        '-loglevel',
        'debug',
        '-i',
        video_input,
        '-vf',
        'scale={:d}:-1,fps=fps={:d}'.format(resize, fps),
        'image/%06d.jpg',
    ]

    """
    process_encoding = process_encoding or \
        ('cp949' if os.name == 'nt' else 'utf-8')
    logger.info('[extract]: process_encoding: %s', process_encoding)

    max_frames_str = '__none__' if max_frames is None else '/{:06d}{:s}'.format(
        max_frames + 1, output_file_type)

    vf_options = ''

    if not extract_all_frames:
        # NOTE: single backslash in single quote
        vf_options += r',select=eq(pict_type\,PICT_TYPE_I)'

    if rotate:
        if rotate == -90:
            vf_options += ',transpose=2'
        if rotate == 90:
            vf_options += ',transpose=1'
        if rotate == 180:
            vf_options += ',transpose=2,transpose=2'

    if width or height:
        width = width or -1
        height = height or -1
        vf_options += ',scale={:d}:{:d}'.format(width, height)

    if fps:
        vf_options += ',fps=fps={:f}'.format(fps)

    logger.info('[extract]: vf_options: %s', vf_options[1:])

    file_pattern = '{:s}/%06d{:s}'.format(output_dir, output_file_type)

    logger.info('[extract]: file_pattern: %s', file_pattern)

    command = [
        'ffmpeg',
        '-loglevel',
        'debug',
        '-i',
        input_file,
    ]

    if vf_options:
        command.extend(['-vf', vf_options[1:]])
        if not extract_all_frames:
            command.extend(['-q:v', '1', '-vsync', '2'])

    command.extend([
        '-f',
        'image2',
        file_pattern,
    ])

    logger.info('[extract]: ffmpeg_command: %s', command)

    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def _emit(line, proc, timecodehandle=None):
        logger.debug('[extract]: %s', line)

        timecode_pattern = r"^.* n:([0-9.]*) .* -> select:1\..*"
        m = re.match(timecode_pattern, line)
        if m:
            timecode = str(m.group(1))
            if timecodehandle:
                print(timecode, file=timecodehandle)

        report_pattern = '00{:s}'.format(output_file_type)  # 00.png 만 출력

        imagename_pattern = r"^\[image2 @ [x0-9a-f]+\] Opening '([^']+\d+\.{:s})' for writing".format(
            output_file_type[1:])
        m = re.match(imagename_pattern, line)
        if m:
            next_im_name = str(m.group(1))
            if next_im_name.endswith(report_pattern):
                logger.info('[extract]: %s', next_im_name)
            if proc and max_frames_str in next_im_name:
                proc.terminate()

    with open(join(output_dir, 'timecodes.txt'), 'w') as timecodehandle:
        while proc.poll() is None:
            line = proc.stdout.readline(4000)
            if not line:
                break
            line = line.rstrip().decode(process_encoding)
            _emit(line, proc, timecodehandle=timecodehandle)

        line, _ = proc.communicate()
        line = line.rstrip().decode(process_encoding)
        _emit(line, None, timecodehandle=timecodehandle)

    logger.info('[extract]: EOF')


if __name__ == '__main__':
    # rdkit_movie_frames(input_file,output_dir,output_file_type='.png',only_i_frames=True,rotate=0,width=None,height=None,fps=None,process_encoding=None)
    from os.path import isdir, join, splitext
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--output_file_type', default='.png')
    parser.add_argument('--extract_all_frames', action='store_true')
    parser.add_argument('--rotate', type=int, default=0)
    parser.add_argument('--width', type=int, default=None)
    parser.add_argument('--height', type=int, default=None)
    parser.add_argument('--fps', type=float, default=None)
    parser.add_argument('--process_encoding', type=str, default=None)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--max_frames', default=None)
    args = parser.parse_args()
    if args.output_dir is None:
        dir_ = splitext(args.input_file)[0]
        args.output_dir = dir_ + '.frames'
    if not isdir(args.output_dir):
        os.makedirs(args.output_dir)
    with open(join(args.output_dir, 'timecodes.txt'), 'w') as timecodehandle:
        args.timecodehandle = timecodehandle
        movie_extract_keyframes(**vars(args))

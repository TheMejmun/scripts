#!/bin/bash
set -e

movie=$1

ffmpeg -i "$movie" -map_metadata -1 -codec copy ''"$movie"'.tmp'

echo hi
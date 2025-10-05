#!/bin/bash

# Optimize images for web using ImageMagick
# Resizes to max width 1280px, strips metadata, compresses to 85% quality, progressive JPEG

magick /Users/karan/Code/website/static/images/homelab-gatus.png -resize 1280x -strip -quality 85 -interlace Plane /Users/karan/Code/website/static/images/homelab-gatus.png

magick /Users/karan/Code/website/static/images/homelab-technitium.png -resize 1280x -strip -quality 85 -interlace Plane /Users/karan/Code/website/static/images/homelab-technitium.png

magick /Users/karan/Code/website/static/images/homelab-beszel-1.png -resize 1280x -strip -quality 85 -interlace Plane /Users/karan/Code/website/static/images/homelab-beszel-1.png

magick /Users/karan/Code/website/static/images/homelab-healthcheck.png -resize 1280x -strip -quality 85 -interlace Plane /Users/karan/Code/website/static/images/homelab-healthcheck.png
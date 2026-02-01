#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow"]
# ///
"""
OG Image Generator for mrkaran.dev

Generates social preview images for blog posts that don't have a custom og_preview_img.
Uses the blog's warm terracotta aesthetic with clean, modern typography.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Configuration
CONFIG = {
    "author": "Karan Sharma",
    "site": "mrkaran.dev",
    "width": 1200,
    "height": 630,
    "padding": 72,
    # Warm, modern color palette matching the blog
    "bg_color": "#1C1917",  # Dark stone
    "title_color": "#FAFAF9",  # Off-white
    "desc_color": "#A8A29E",  # Muted stone
    "accent_color": "#FB923C",  # Warm orange accent
    "author_color": "#78716C",  # Subtle gray
}

CACHE_VERSION = 3


class OGImageGenerator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.content_dir = project_root / "content" / "posts"
        self.output_dir = project_root / "static" / "images" / "og"
        self.cache_file = project_root / ".og_cache.json"
        self.cache = self._load_cache()

        self.width = CONFIG["width"]
        self.height = CONFIG["height"]
        self.padding = CONFIG["padding"]
        self.content_width = self.width - (2 * self.padding)

        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """Load fonts with fallbacks."""
        fonts = {}

        # Try to find good fonts, fall back to default
        font_paths = [
            # macOS
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/SF-Pro-Display-Bold.otf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ]

        regular_paths = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/SF-Pro-Display-Regular.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]

        bold_font = None
        regular_font = None

        for path in font_paths:
            if Path(path).exists():
                bold_font = path
                break

        for path in regular_paths:
            if Path(path).exists():
                regular_font = path
                break

        try:
            if bold_font:
                fonts["title_large"] = ImageFont.truetype(bold_font, 64)
                fonts["title_medium"] = ImageFont.truetype(bold_font, 52)
                fonts["title_small"] = ImageFont.truetype(bold_font, 44)
            else:
                fonts["title_large"] = ImageFont.load_default()
                fonts["title_medium"] = ImageFont.load_default()
                fonts["title_small"] = ImageFont.load_default()

            if regular_font:
                fonts["desc"] = ImageFont.truetype(regular_font, 28)
                fonts["author"] = ImageFont.truetype(regular_font, 24)
            else:
                fonts["desc"] = ImageFont.load_default()
                fonts["author"] = ImageFont.load_default()

        except Exception as e:
            print(f"Warning: Font loading failed ({e}), using defaults")
            fonts["title_large"] = ImageFont.load_default()
            fonts["title_medium"] = ImageFont.load_default()
            fonts["title_small"] = ImageFont.load_default()
            fonts["desc"] = ImageFont.load_default()
            fonts["author"] = ImageFont.load_default()

        return fonts

    def _load_cache(self) -> dict:
        """Load generation cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_cache(self):
        """Save generation cache."""
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def _content_hash(self, title: str, description: str) -> str:
        """Generate hash for caching."""
        content = f"{CACHE_VERSION}:{title}:{description}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _parse_frontmatter(self, content: str) -> dict | None:
        """Parse TOML frontmatter from markdown file."""
        match = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+", content, re.DOTALL)
        if not match:
            return None

        frontmatter = {}
        fm_content = match.group(1)

        # Simple TOML parsing for what we need
        for line in fm_content.split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("["):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                frontmatter[key] = value

        # Check for og_preview_img in [extra] section
        if "[extra]" in fm_content:
            extra_match = re.search(r"\[extra\](.*?)(?=\[|$)", fm_content, re.DOTALL)
            if extra_match:
                for line in extra_match.group(1).split("\n"):
                    line = line.strip()
                    if line.startswith("og_preview_img"):
                        frontmatter["og_preview_img"] = (
                            line.split("=", 1)[1].strip().strip('"').strip("'")
                        )

        return frontmatter

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
        """Wrap text to fit within max_width."""
        if not text:
            return []

        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _get_title_font(self, title: str):
        """Select font size based on title length."""
        if len(title) <= 35:
            return self.fonts["title_large"]
        elif len(title) <= 60:
            return self.fonts["title_medium"]
        else:
            return self.fonts["title_small"]

    def _text_height(self, text: str, font) -> int:
        """Get height of rendered text."""
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    def generate_image(self, title: str, description: str, output_path: Path):
        """Generate the OG image."""
        img = Image.new("RGB", (self.width, self.height), CONFIG["bg_color"])
        draw = ImageDraw.Draw(img)

        # Draw accent bar at top
        draw.rectangle([(0, 0), (self.width, 6)], fill=CONFIG["accent_color"])

        y = self.padding + 24

        # Draw title
        title_font = self._get_title_font(title)
        title_lines = self._wrap_text(title, title_font, self.content_width)

        for i, line in enumerate(title_lines[:3]):  # Max 3 lines
            draw.text(
                (self.padding, y), line, fill=CONFIG["title_color"], font=title_font
            )
            y += self._text_height(line, title_font) + 12

        y += 24

        # Draw description
        if description:
            desc_font = self.fonts["desc"]
            desc_lines = self._wrap_text(description, desc_font, self.content_width)

            for line in desc_lines[:3]:  # Max 3 lines
                draw.text(
                    (self.padding, y), line, fill=CONFIG["desc_color"], font=desc_font
                )
                y += self._text_height(line, desc_font) + 8

        # Draw author/site at bottom
        author_font = self.fonts["author"]
        author_text = f"{CONFIG['author']}  •  {CONFIG['site']}"

        author_y = self.height - self.padding - 24
        draw.text(
            (self.padding, author_y),
            author_text,
            fill=CONFIG["author_color"],
            font=author_font,
        )

        # Draw subtle accent dot
        draw.ellipse(
            [
                (self.width - self.padding - 8, author_y + 6),
                (self.width - self.padding, author_y + 14),
            ],
            fill=CONFIG["accent_color"],
        )

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", optimize=True)

    def process_posts(self) -> tuple[int, int, int]:
        """Process all posts and generate missing OG images."""
        generated = 0
        skipped_custom = 0
        skipped_cached = 0

        self.output_dir.mkdir(parents=True, exist_ok=True)

        for md_file in self.content_dir.glob("*.md"):
            if md_file.name == "_index.md":
                continue

            content = md_file.read_text()
            fm = self._parse_frontmatter(content)

            if not fm or not fm.get("title"):
                continue

            # Skip if custom og_preview_img is set
            if fm.get("og_preview_img"):
                skipped_custom += 1
                continue

            title = fm.get("title", "")
            description = fm.get("description", "")
            slug = md_file.stem
            output_path = self.output_dir / f"{slug}.png"

            # Check cache
            content_hash = self._content_hash(title, description)
            cache_key = str(output_path.relative_to(self.project_root))

            if output_path.exists() and self.cache.get(cache_key) == content_hash:
                skipped_cached += 1
                continue

            # Generate image
            print(f"  Generating: {slug}.png")
            self.generate_image(title, description, output_path)
            self.cache[cache_key] = content_hash
            generated += 1

        self._save_cache()
        return generated, skipped_custom, skipped_cached


def main():
    project_root = Path(__file__).parent.parent

    print("Generating OG images...")
    generator = OGImageGenerator(project_root)
    generated, skipped_custom, skipped_cached = generator.process_posts()

    print(
        f"Done: {generated} generated, {skipped_custom} have custom images, {skipped_cached} cached"
    )


if __name__ == "__main__":
    main()

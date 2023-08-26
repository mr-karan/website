+++
title = "Useful sed Command Snippets for Linux"
date = 2022-06-12
type = "til"
description = "A collection of useful sed command snippets for text processing in Linux."
in_search_index = true
[taxonomies]
tags = ["Linux", "Snippets"]
+++

## Edit in place

`sed -i 's/STRING_TO_REPLACE/STRING_TO_REPLACE_IT/g' filename`

## Match only the word

`\b` in regex is used to match word boundaries (i.e. the location between the first word character and non-word character).

`sed -i 's/\bsuper_specific_phrase\b/STRING_TO_REPLACE_IT/g' filename`

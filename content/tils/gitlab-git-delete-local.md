+++
title = "Clean Up Outdated Local Git Branches"
date = 2023-08-16
type = "til"
description = "Step-by-step guide to deleting stale local branches in Git that no longer exist in the upstream repository."
in_search_index = true
[taxonomies]
tags = ["git", "snippets"]
+++

To delete local branches that don't exist in the upstream repository anymore, you can follow these steps:

1. **Ensure you're up-to-date**:
   First, fetch the latest changes from the upstream:

   ```bash
   git fetch --prune
   ```

   The `--prune` option will remove any remote-tracking references that no longer exist on the remote. This will help you ensure that you know which branches are truly gone from the upstream.

2. **List merged branches**:
   You can see which branches are already merged into your current branch with:

   ```bash
   git branch --merged
   ```

   This will show you a list of branches that are safe to delete because their changes are already included in the current branch.

3. **Delete merged branches**:
   If you're sure that the branches listed in step 2 are no longer needed (and you've checked that they don't contain any unique work), you can delete them.

   ```bash
   git branch --merged | egrep -v "(^\*|master|main)" | xargs git branch -d
   ```

   - The `egrep -v "(^\*|master|main)"` part of this command ensures that you don't try to delete the currently checked out branch (`*`) or typically important branches like `master` or `main`.

   - The `xargs git branch -d` part of the command will attempt to delete each branch that's passed to it. The `-d` flag ensures that Git will only delete the branch if it's been merged. If you're absolutely sure you want to force deletion, you can use the `-D` flag instead, but be careful with it.

4. **Optional**:
   To verify that you've successfully deleted the old local branches, you can list all your local branches with:

   ```bash
   git branch
   ```

By following these steps, you'll clean up your local branches, removing the ones that don't exist in the upstream repository anymore. Always be cautious when deleting branches to ensure you don't lose any important work.
+++
title = "Resolving UUID Conflicts when Mounting AWS EBS Volumes"
date = 2023-08-31
type = "til"
description = "A guide on troubleshooting UUID conflicts during the mounting of Amazon EBS volumes. Learn about the `-o nouuid` option and how to identify existing UUID conflicts."
in_search_index = true
[taxonomies]
tags = ["AWS"]
+++


Today I Learned (TIL) about an interesting issue that can occur when mounting Amazon EBS volumes created from snapshots. The problem arises from UUID conflicts which can prevent the mounting process.

When you create an EBS volume from a snapshot, the new volume inherits the UUID of the original filesystem. If the original volume is still mounted on the same instance, this can cause a UUID conflict when you try to mount the new volume.

Let's say you're trying to mount a volume with XFS filesystem:

```bash
sudo mount -t xfs /dev/nvme2n1 /backup-check
```

And you encounter an error like this:

```bash
mount: /backup-check: wrong fs type, bad option, bad superblock on /dev/nvme2n1, missing codepage or helper program, or other error.
```

The issue might be due to a UUID conflict. To resolve this, you can use the `-o nouuid` option when mounting the volume:

```bash
sudo mount -t xfs -o nouuid /dev/nvme2n1 /backup-check
```

The `-o nouuid` option tells the mount command to ignore the UUID of the filesystem. This allows the volume to be mounted even if another volume with the same UUID is already mounted.

---

## Check UUID

You can check the UUID of a filesystem using the `blkid` command:

```bash
sudo blkid /dev/nvme2n1
```

This command will output something like this:

```bash
/dev/nvme2n1: UUID="1234abcd-12ab-34cd-56ef-123456abcdef" TYPE="xfs"
```

You can compare the UUIDs of your volumes to see if there's a conflict.

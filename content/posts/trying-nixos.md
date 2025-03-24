+++
title = "Trying out NixOS"
date = 2025-03-23T10:15:00+05:30
type = "post"
description = "Exploring NixOS for the first time"
in_search_index = true
[taxonomies]
tags = ["Nix"]
+++

I've been introduced to Nix by my colleagues at work. Being a Linux user for over a decade and a serial distro hopper, I was curious to learn more about it. I’d seen Nix mentioned before, but the comments about its steep learning curve made me wonder if the effort was worth it. I decided to give it a try by reading this excellent [beginner's guide](https://nixos-and-flakes.thiscute.world) however got bored very quickly and decided to "learn on the fly". I spun up a VM in my homelab to install NixOS using their [official GUI installer image](https://nixos.org/download/).

## Installation & First Impressions

The installation was as straightforward as any other Linux distro. NixOS is a declarative operating system that leverages the Nix functional package manager and a rich ecosystem of Nix packages. The flexibility is mind-blowing: you can configure everything—from user accounts and SSH keys to `$SHELL` config and plugins entirely through code.

Once installed, the first place you'd want to poke around is the `/etc/nixos` directory, which contains two essential configuration files:

- `hardware-configuration.nix`: Generated during installation (or regenerated with commands like `nixos-generate-config`), it has hardware-specific details such as filesystem mount points, disk configurations, kernel modules etc. See an example file [here](https://github.com/fooblahblah/nixos/blob/master/hardware-configuration.nix).

- `configuration.nix`: This is _the most_ important file you want to start editing with. Here you define system-wide settings like timezone, locale, user accounts, and networking. Everything is declared in one place, making your system’s state reproducible.

### First Configuration Changes

When I opened the terminal, I immediately noticed that `vim` wasn’t installed. So, I updated my `configuration.nix` to include the packages I needed:

```nix
environment.systemPackages = with pkgs; [
  git
  vim
];
```

After saving, I ran:

```bash
sudo nixos-rebuild switch
```

This rebuilds the system using the new declarative configuration.

## Version Control & Flakes

Next, I wanted to set up version control for my Nix configurations. The key takeaway is that while the system’s state is revertable in NixOS, your personal data (which includes `configuration.nix`) isn’t automatically backed up. You must manage your own version history for your Nix configs. Since I was tweaking with no knowledge of Nix, having a version history was crucial.

I moved my `/etc/nixos` configs to `~/Code/nixos-configs` and initialized a Git repository:

```bash
# Create repo in home directory (better than root-owned /etc/nixos)
mkdir ~/nixos-config
cp -r /etc/nixos/* ~/nixos-config/
cd ~/nixos-config

# Initialize Git
git init
git add .
git commit -m "Initial NixOS configuration"

# Add GitHub remote
git remote add origin https://github.com/username/nixos-config.git
git push -u origin main
```

Here's how `flake.nix` looks:

```nix
{
  description = "NixOS configuration for Karan's homelab, servers, and personal dev machines";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    
    # Add agenix as an input
    agenix = {
      url = "github:ryantm/agenix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # Optionally add other inputs like home-manager
    # home-manager = {
    #   url = "github:nix-community/home-manager/release-24.11";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };
  };

  outputs = { self, agenix, nixpkgs, ... }@inputs: {
    # Make agenix available as a package
    packages.x86_64-linux.agenix = agenix.packages.x86_64-linux.default;
    
    nixosConfigurations.work = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ./configuration.nix
        agenix.nixosModules.default  # Add agenix module
      ];
    };
  };
}
```

### A Note on Flakes

Flakes are an experimental (although widely adopted in the community) feature in Nix that bring reproducibility, composability, and a standardized structure to your configurations and package definitions. They allow you to declare all inputs (like nixpkgs, home-manager, or other repositories) and outputs (such as system configurations, packages, or development shells) in a single file. Flakes also create a lock file (`flake.lock`) that pins your dependencies to specific revisions, ensuring that your builds remain reproducible over time.

I learned the hard way that—even for local configurations you must commit your files. Otherwise, you may see errors like:

```bash
path '/nix/store/...source/flake.nix' does not exist
```

Even if you're using local paths and have no intention to push to `git`, you still need `git init` && `git add` for flakes to work.
From whatever google-fu I did, it seems this requirement is to ensure that flakes can reliably reference the exact content in your configuration.
I am sure there might be good reasons for it (as I said before, I've skipped RTFMing altogether ^_^), but atleast the errors can be more verbose/helpful.

And why I skipped docs: Remember, we're on a mission to get things up and running with Nix and then _later_ spend time about reading their internals if it actually proves to be a valuable experiment.

## Switching Channels

While installing packages, I noticed some packages were quite outdated. That’s when I learned about NixOS channels. Think of channels as analogous to LTS releases. For faster updates, you can switch to the `unstable` channel. Although the name sounds intimidating, it simply means you’ll receive more frequent package updates.

To do this, you can edit your `flake.nix` and switch the URL to an unstable channel:

```bash
  inputs = {
    - nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11"; # Stable channel
    + nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # Unstable channel
  };
```

## Firmware Updates

After setting up packages, it was time to configure firmware updates using `fwupd—essential` for keeping your hardware up to date.

I asked Claude to help me for a quick setup. Here’s what I did:

```nix
{ config, pkgs, ... }:

{
  services.fwupd.enable = true;
}
```

Then run a rebuild:

```bash
sudo nixos-rebuild switch
```

Once enabled, you can use the `fwupdmgr` command-line tool to manage firmware updates:

```bash
# Refresh metadata and check for available updates
fwupdmgr refresh
fwupdmgr get-updates
# Install available firmware updates
fwupdmgr update
```

## Fine Tuning

I also tweaked some settings for the Nix package manager to optimize builds, caching, and overall performance. Here’s a snippet from my configuration:

```bash
  # Nix package manager optimizations
  nix = {
    settings = {
      # Optimize store to remove duplicate files
      auto-optimise-store = true;

      # Allow building multiple derivations in parallel
      max-jobs = "auto";

      # Number of parallel build tasks per job
      cores = 0; # 0 means use all available cores

      # Use the binary cache aggressively
      substituters = [
        "<https://cache.nixos.org>"
        "<https://nix-community.cachix.org>"
        "<https://nixpkgs-wayland.cachix.org>"
      ];

      # Optimize fetching from GitHub
      connect-timeout = 5;

      # Prevent unneeded rebuilds
      commit-lockfile-summary = "Update flake.lock";
    };

    # Garbage collection settings
    gc = {
      automatic = true;
      dates = "weekly";
      options = "--delete-older-than 30d";
    };

    # Optimize builds using different build cores
    buildCores = 0; # 0 means use all available cores

    # Enable flakes and modern Nix command features
    extraOptions = ''
      experimental-features = nix-command flakes
      warn-dirty = false
      keep-going = true
      log-lines = 20
    '';
  };
```

## Escape Hatches

So far things seems all rosy. Within just spending a couple of minutes - I had a perfectly working machine for myself - and the best part - all reproducible with a single command. I was starting to see why people who use NixOS preach about it so much.

However, not everything is smooth when you deviate from the happy path. For instance, I use [Aider](/posts/using-llm/) for LLM assisted programming, but the version on Nixpkgs was about [three minor versions](https://github.com/NixOS/nixpkgs/blob/nixos-unstable/pkgs/development/python-modules/aider-chat/default.nix#L16) behind. Typically for any other software, I wouldn't have cared so much - however with these LLM tools, a lot changes rapidly and I didn't want to stay behind. Besides, it seemed like a fun exercise in getting my hands dirty by installing a Python package on NixOS which turned out to be quite tricky because Nix is absurdly obsessive about fully isolated builds.

Here's an example flake that I used for attempting to install Aider with `uv`  in a dev shell (which didn't work btw):

```nix
{
  description = "Aider development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            python312
            uv
          ];
          shellHook = ''
            export PATH="$HOME/.local/bin:$PATH"
          '';
        };
      }
    );
}
```

Entering the dev shell with `nix develop` and installing Aider with `uv`:

```bash
uv tool install --force --python python3.12 aider-chat@latest
```


However, I ran into this error:

```bash
"/home/karan/.local/share/uv/tools/aider-chat/lib/python3.12/site-packages/litellm/litellm_core_uti
ls/llm_cost_calc/utils.py", line 9, in <module>
    from litellm.utils import get_model_info
  File
"/home/karan/.local/share/uv/tools/aider-chat/lib/python3.12/site-packages/litellm/utils.py", line
53, in <module>
    from tokenizers import Tokenizer
  File
"/home/karan/.local/share/uv/tools/aider-chat/lib/python3.12/site-packages/tokenizers/__init__.py",
line 78, in <module>
    from .tokenizers import (
ImportError: libstdc++.so.6: cannot open shared object file: No such file or directory
```

The error indicated that Aider was missing a required dependency `libstdc++.so.6` which is a part of the C++ standard library needed by the tokenizers package. To fix this, I added `stdenv.cc.cc.lib` (and even `gcc` to be on the safer side) to my `buildInputs`. This is because while `uv` installs Python packages, it doesn’t handle system-level dependencies. In a Nix environment, every dependency, including system libraries, must be explicitly specified.

Frankly, Python’s packaging ecosystem is still a mess. Although tools like `uv` help, achieving a completely isolated build, especially when shared libraries are involved is challenging. I wish the Python community would put more effort into resolving these issues.

While I was able to make `aider` work by explicitly adding all the dependencies, I faced another outdate package: `code-cursor`. Since this is a full blown electron app, I didn't wish to package this myself.

After some frustration, I tried using [Distrobox](https://distrobox.it/) as recommended by a [colleague](https://blog.trieoflogs.com/). Distrobox lets you run containers that feel almost like a native OS by managing user IDs, host mounts, network interfaces, and more. I used an Arch Linux image, installed `cursor-bin` from the AUR, and everything worked fine. Well mostly:

- Fonts were missing. So, if I want to use custom fonts in my IDE - I need to have them installed in the container as well.
- Since my `fish` shell config had `export EDITOR=nvim`, I had to install `neovim` in the container as well, otherwise, I'd get an error when trying to `git commit` etc. There's an option to customise the [shell](https://distrobox.it/useful_tips/#use-a-different-shell-than-the-host) in distrobox, but for whatever reason (that I didn't want to debug), it didn't work for me.

Yet, something still felt off. The whole point of using NixOS is to achieve a fully declarative and reproducible setup. Resorting to an escape hatch like Distrobox undermines that goal. So I was very conflicted about this. I'm sure there's a better way to handle these situations, and I should probably read the docs to find out.

## Final Thoughts

I’m definitely sold on running NixOS, especially when managing multiple systems. With a single declarative file (`configuration.nix`), duplicating your setup across machines becomes effortless. No more "documenting" (or rather _forgetting_ to document and keeping it updated)- as the config is the single source of truth.

Fun fact: I even messed up my NixOS build by misconfiguring the `hardware-configuration.nix`, and my system became unusable even after a reboot, it couldn’t mount the filesystem on the correct device. In other distros, that would have sent me into panic mode, but with NixOS, all I had to do was revert to the previous working state, and everything was fine. That was so cool!

I’m definitely considering moving my homelab to NixOS in the coming few days because I honestly see the value for a server setup. I often set up my personal server and then forget everything I’ve done and I’m always scared of touching or creating a new server from scratch. I even created a [small shell script installer](https://github.com/mr-karan/junbi) to help me for getting a base system ready. But like this shell script or even tools such as Ansible - they are all idempotent in nature. However in Nix, if I remove a certain piece from the configuration, there isn’t a trace of it left on the system. That makes it truly declarative and reproducible - unlike Ansible where you can still have some parts of the old setup.

However, for my primary machine at work, I’ll wait on the sidelines until the packages I depend on resolve their dependency issues and I get a chance to read up more on the escape hatches I tried to see if there’s a more streamlined way of doing things. I might be missing a lot of fundamental details since I skipped the docs entirely to get my hands dirty. But now that I see the value of a declarative system and especially how easy it is to roll back the machine to a previously known good state, I’m motivated to read up more on this and might post an update to this blog.

Fin! 

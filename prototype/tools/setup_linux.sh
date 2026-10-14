#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo "This helper is for Linux x86_64. Install Godot 4.5.1 and Blender 4.5.3 for your platform." >&2
  exit 1
fi

install_dir="$HOME/.local/share/graphics-tools"
bin_dir="$HOME/.local/bin"
mkdir -p "$install_dir" "$bin_dir"

if [[ ! -x "$install_dir/Godot_v4.5.1-stable_linux.x86_64" ]]; then
  curl -fL --retry 2 https://github.com/godotengine/godot/releases/download/4.5.1-stable/Godot_v4.5.1-stable_linux.x86_64.zip -o "$install_dir/godot.zip"
fi
if [[ -f "$install_dir/godot.zip" ]]; then
  echo "5bccbed65a94b82c7c319fdb15719ee8113a6e503976cc54e16f1c61fe95f3d74e5e40b8449b5bb89ff7f424574c20af01a4f5ef08b389e4dc338b245185b0b9  $install_dir/godot.zip" | sha512sum -c -
  unzip -qo "$install_dir/godot.zip" -d "$install_dir"
fi
if [[ ! -x "$install_dir/blender-4.5.3-linux-x64/blender" ]]; then
  curl -fL --retry 2 https://download.blender.org/release/Blender4.5/blender-4.5.3-linux-x64.tar.xz -o "$install_dir/blender.tar.xz"
  echo "975c58fcb244273838534bba771e64ad87739216b0f9b39a888531a49a72d845  $install_dir/blender.tar.xz" | sha256sum -c -
  tar -xf "$install_dir/blender.tar.xz" -C "$install_dir"
fi
ln -sfn "$install_dir/Godot_v4.5.1-stable_linux.x86_64" "$bin_dir/godot"
ln -sfn "$install_dir/blender-4.5.3-linux-x64/blender" "$bin_dir/blender"
echo "Installed pinned tools in $bin_dir. Add that directory to PATH if necessary."

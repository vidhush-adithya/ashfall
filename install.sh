#!/usr/bin/env bash
# ╔════════════════════════════════════════════════════╗
# ║  ASHFALL installer — niri rice for CTF operators    ║
# ║  Arch Linux. Run as your normal user (uses sudo).   ║
# ║    ./install.sh            full install             ║
# ║    ./install.sh --no-ctf   desktop only             ║
# ║    ./install.sh --dots     configs only, no pkgs    ║
# ╚════════════════════════════════════════════════════╝
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
BACKUP="$HOME/.config/ashfall-backup-$(date +%Y%m%d-%H%M%S)"
WITH_CTF=1; WITH_PKGS=1
for a in "$@"; do case "$a" in --no-ctf) WITH_CTF=0;; --dots) WITH_PKGS=0;; esac; done

c1=$'\e[38;2;139;90;60m'; c2=$'\e[38;2;110;102;87m'; c3=$'\e[38;2;154;131;72m'; cr=$'\e[38;2;160;82;63m'; r=$'\e[0m'
say()  { echo "${c1}▌${r} $*"; }
warn() { echo "${cr}▌ $*${r}"; }
ask()  { read -rp "${c3}▌ $* [y/N] ${r}" x; [[ "$x" =~ ^[Yy] ]]; }

cat <<EOF
${c1}
    ▄▀█ █▀ █░█ █▀▀ ▄▀█ █░░ █░░
    █▀█ ▄█ █▀█ █▀░ █▀█ █▄▄ █▄▄${r}
${c2}    niri // ctf operator rice // no bright colours survived${r}

EOF
[ "$EUID" -eq 0 ] && { warn "run as your normal user, not root"; exit 1; }
command -v pacman >/dev/null || { warn "this installer is for Arch Linux"; exit 1; }

DESKTOP=(
  niri xwayland-satellite xdg-desktop-portal-gnome xdg-desktop-portal-gtk
  waybar fuzzel mako swaybg swaylock swayidle kitty polkit-gnome
  wl-clipboard cliphist libnotify brightnessctl playerctl pavucontrol
  networkmanager network-manager-applet pipewire wireplumber pipewire-pulse
  ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji papirus-icon-theme adw-gtk-theme
  zsh zsh-autosuggestions zsh-syntax-highlighting starship fzf zoxide eza bat
  ripgrep fd jq neovim yazi btop fastfetch firefox unzip p7zip
)
CTF=(
  # pwn / rev
  gdb pwndbg python-pwntools ropgadget checksec patchelf ltrace strace
  radare2 ghidra imhex hexyl upx
  # web / net
  nmap wireshark-qt ffuf gobuster sqlmap openbsd-netcat socat rlwrap
  openvpn wireguard-tools tcpdump whois bind
  # crypto / cracking
  john hashcat hydra python-pycryptodome python-gmpy2 python-sympy z3 python-z3-solver
  # forensics / stego
  binwalk perl-image-exiftool foremost sleuthkit testdisk
  # python & containers
  python-requests python-beautifulsoup4 python-pip python-pipx docker docker-compose
)
AUR_CTF=(burpsuite seclists stegseek volatility3 wordlists)

install_pkgs() {
  local repo=() aur=() p
  for p in "$@"; do
    if pacman -Si "$p" &>/dev/null; then repo+=("$p"); else aur+=("$p"); fi
  done
  if ((${#repo[@]})); then
    say "pacman: ${#repo[@]} packages"
    sudo pacman -S --needed --noconfirm "${repo[@]}" || warn "some pacman packages failed — continuing"
  fi
  ((${#aur[@]})) && AUR_QUEUE+=("${aur[@]}")
}

aur_helper() {
  command -v paru >/dev/null && { echo paru; return; }
  command -v yay  >/dev/null && { echo yay;  return; }
  if ask "no AUR helper found. build paru now?"; then
    sudo pacman -S --needed --noconfirm base-devel git >/dev/null
    local t; t=$(mktemp -d); git clone -q https://aur.archlinux.org/paru-bin.git "$t/paru" \
      && (cd "$t/paru" && makepkg -si --noconfirm) && echo paru
  fi
}

if ((WITH_PKGS)); then
  say "syncing package databases"
  sudo pacman -Sy --noconfirm >/dev/null
  AUR_QUEUE=()
  install_pkgs "${DESKTOP[@]}"
  if ((WITH_CTF)); then
    install_pkgs "${CTF[@]}"
    AUR_QUEUE+=("${AUR_CTF[@]}")
  fi
  if ((${#AUR_QUEUE[@]})); then
    say "AUR: ${AUR_QUEUE[*]}"
    H=$(aur_helper)
    if [ -n "${H:-}" ]; then
      "$H" -S --needed --noconfirm "${AUR_QUEUE[@]}" || warn "some AUR packages failed — install them later with: $H -S <pkg>"
    else
      warn "skipped AUR packages: ${AUR_QUEUE[*]}"
    fi
  fi
  if ((WITH_CTF)); then
    getent group wireshark >/dev/null && sudo usermod -aG wireshark "$USER"
    getent group docker    >/dev/null && sudo usermod -aG docker "$USER"
    [ -f /usr/share/wordlists/rockyou.txt.tar.gz ] && sudo tar -xzf /usr/share/wordlists/rockyou.txt.tar.gz -C /usr/share/wordlists/ 2>/dev/null
    # pwndbg: hook into gdb if the package didn't
    if [ -f /usr/share/pwndbg/gdbinit.py ] && ! grep -q pwndbg "$HOME/.gdbinit" 2>/dev/null; then
      echo "source /usr/share/pwndbg/gdbinit.py" >> "$HOME/.gdbinit"
    fi
  fi
  sudo systemctl enable --now NetworkManager >/dev/null 2>&1 || true
fi

# ── configs (backup first) ──────────────────────────────────────────
say "backing up existing configs → $BACKUP"
mkdir -p "$BACKUP"
for d in niri waybar fuzzel mako kitty swaylock btop ashfall starship.toml; do
  [ -e "$CFG/$d" ] && cp -a "$CFG/$d" "$BACKUP/"
done

say "deploying configs"
mkdir -p "$CFG" "$HOME/.local/bin" "$HOME/.local/share/ashfall" "$HOME/Pictures/Screenshots" "$HOME/ctf"
cp -a "$HERE/config/niri" "$HERE/config/waybar" "$HERE/config/fuzzel" "$HERE/config/mako" \
      "$HERE/config/kitty" "$HERE/config/swaylock" "$HERE/config/ashfall" "$CFG/"
mkdir -p "$CFG/btop/themes" && cp "$HERE/config/btop/themes/ashfall.theme" "$CFG/btop/themes/"
if [ -f "$CFG/btop/btop.conf" ]; then
  sed -i 's/^color_theme = .*/color_theme = "ashfall"/' "$CFG/btop/btop.conf"
else
  printf 'color_theme = "ashfall"\ntheme_background = False\n' > "$CFG/btop/btop.conf"
fi
cp "$HERE/config/starship.toml" "$CFG/starship.toml"
install -m 755 "$HERE"/bin/* "$HOME/.local/bin/"
chmod +x "$CFG/waybar/scripts/"*.sh
cp "$HERE"/wallpapers/*.png "$HOME/.local/share/ashfall/"

sed -i "s|~/.local/share/ashfall/ashfall-lock.png|$HOME/.local/share/ashfall/ashfall-lock.png|" "$CFG/swaylock/config"

# zsh: append one source line, never overwrite the user's .zshrc
touch "$HOME/.zshrc"
grep -q 'ashfall/ashfall.zsh' "$HOME/.zshrc" || echo '[ -f ~/.config/ashfall/ashfall.zsh ] && source ~/.config/ashfall/ashfall.zsh' >> "$HOME/.zshrc"

# GTK dark everywhere
mkdir -p "$CFG/gtk-3.0" "$CFG/gtk-4.0"
for v in 3.0 4.0; do
  [ -f "$CFG/gtk-$v/settings.ini" ] && cp "$CFG/gtk-$v/settings.ini" "$BACKUP/gtk-$v-settings.ini"
  printf '[Settings]\ngtk-theme-name=adw-gtk3-dark\ngtk-icon-theme-name=Papirus-Dark\ngtk-font-name=Noto Sans 10\ngtk-application-prefer-dark-theme=1\n' > "$CFG/gtk-$v/settings.ini"
done
if command -v gsettings >/dev/null; then
  gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null
  gsettings set org.gnome.desktop.interface gtk-theme 'adw-gtk3-dark' 2>/dev/null
  gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark' 2>/dev/null
  gsettings set org.gnome.desktop.interface monospace-font-name 'JetBrainsMono Nerd Font 11' 2>/dev/null
fi

if command -v niri >/dev/null; then
  if niri validate -c "$CFG/niri/config.kdl" >/dev/null 2>&1; then say "niri config: valid"
  else warn "niri config reported problems:"; niri validate -c "$CFG/niri/config.kdl"; fi
fi

if [ "$(basename "${SHELL:-}")" != "zsh" ] && command -v zsh >/dev/null && ask "make zsh your login shell?"; then
  chsh -s "$(command -v zsh)"
fi

cat <<EOF

${c3}▌ ASHFALL deployed.${r}
${c2}  backup of your old configs: $BACKUP
  if you're inside niri: it reloads on its own — restart waybar with  pkill waybar; waybar &
  otherwise log out and pick "niri" at your display manager (or run  niri-session  from a TTY).
  groups changed (wireshark/docker) → log out & in once.
  press  Super+Shift+/  for every hotkey.${r}
EOF

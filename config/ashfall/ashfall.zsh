# ASHFALL — zsh layer (sourced from ~/.zshrc). Safe to edit.
export EDITOR=nvim
export CTF="$HOME/ctf"
export WL=/usr/share/seclists
export ROCKYOU=/usr/share/wordlists/rockyou.txt
export PATH="$HOME/.local/bin:$PATH"
export BAT_THEME=ansi
export FZF_DEFAULT_OPTS="--color=bg:#0c0b09,bg+:#2a2620,fg:#a89f8c,fg+:#c2b8a3,hl:#9a8348,hl+:#ad9659,border:#4a443a,prompt:#8b5a3c,pointer:#8b5a3c,marker:#5d6a48,info:#6e6657 --border=sharp --height=40%"

HISTFILE=~/.zsh_history; HISTSIZE=100000; SAVEHIST=100000
setopt share_history hist_ignore_dups hist_ignore_space autocd interactive_comments
bindkey -e
autoload -Uz compinit && compinit -d ~/.cache/zcompdump
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

for p in /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh \
         /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh; do
  [ -f "$p" ] && source "$p"
done
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#4a443a'
command -v fzf >/dev/null && source <(fzf --zsh)
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"
command -v starship >/dev/null && eval "$(starship init zsh)"

# ── everyday ─────────────────────────────────────────────
alias ls='eza --group-directories-first' ll='eza -lah --git --group-directories-first' tree='eza -T'
alias cat='bat -pp' grep='grep --color=auto' ip='ip -c'
alias v=nvim

# ── ctf: navigation ──────────────────────────────────────
alias c='cd ~/ctf/current'
alias cn='ctf-new'
alias notes='${EDITOR} ~/ctf/current/notes.md'
myip()  { ctf-ip; }

# ── ctf: recon ───────────────────────────────────────────
nmapq() { mkdir -p nmap && sudo nmap -sC -sV -oA nmap/initial "$@"; }
nmapf() { mkdir -p nmap && sudo nmap -p- --min-rate 3000 -oA nmap/allports "$@"; }
fuzzdir() { ffuf -c -w "$WL/Discovery/Web-Content/raft-medium-directories.txt" -u "${1%/}/FUZZ" "${@:2}"; }
vhosts(){ ffuf -c -w "$WL/Discovery/DNS/subdomains-top1million-20000.txt" -u "http://$1" -H "Host: FUZZ.$1" "${@:2}"; }
serve() { local p=${1:-8000}; echo "→ http://$(ctf-ip 2>/dev/null || hostname -i):$p/"; python3 -m http.server "$p"; }
listen(){ rlwrap nc -lvnp "${1:-4444}"; }

# ── ctf: quick decode / transform ────────────────────────
b64d()  { printf '%s' "$1" | base64 -d; echo; }
b64e()  { printf '%s' "$1" | base64 -w0; echo; }
hexd()  { printf '%s' "$1" | xxd -r -p; echo; }
hexe()  { printf '%s' "$1" | xxd -p | tr -d '\n'; echo; }
rot13() { printf '%s' "$1" | tr 'A-Za-z' 'N-ZA-Mn-za-m'; echo; }
urld()  { python3 -c 'import sys,urllib.parse as u;print(u.unquote_plus(sys.argv[1]))' "$1"; }
urle()  { python3 -c 'import sys,urllib.parse as u;print(u.quote(sys.argv[1],safe=""))' "$1"; }
jwtd()  { python3 -c 'import sys,base64,json
for p in sys.argv[1].split(".")[:2]: print(json.dumps(json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4))),indent=2))' "$1"; }

# ── ctf: files / forensics / rev ─────────────────────────
flagfind() { grep -RaoE "${FLAG_RE:-[A-Za-z0-9_]{2,20}\{[^}[:space:]]{3,200}\}}" "${@:-.}"; }
triage() {  # first look at any file
  local f="$1"; file "$f"; echo; exiftool -q "$f" 2>/dev/null | head -20; echo
  case "$(file -b "$f")" in *ELF*) checksec --file="$f" 2>/dev/null;; esac
  echo "── strings w/ flag-ish / interesting"; strings -n 6 "$f" | grep -iE 'flag|ctf|key|pass|secret|\{' | head -20
  echo "── binwalk"; binwalk "$f" 2>/dev/null | head -15
}
ex() {
  case "$1" in
    *.tar.gz|*.tgz) tar xzf "$1";; *.tar.xz) tar xJf "$1";; *.tar.bz2) tar xjf "$1";;
    *.tar) tar xf "$1";; *.zip) unzip "$1";; *.7z) 7z x "$1";; *.gz) gunzip "$1";;
    *.xz) unxz "$1";; *.bz2) bunzip2 "$1";; *.rar) unrar x "$1" 2>/dev/null || 7z x "$1";;
    *) echo "ex: unknown archive: $1";;
  esac
}
alias gdb='gdb -q'
alias r2='r2 -A'

# ── greeting ─────────────────────────────────────────────
if [[ -o interactive ]] && [[ -z "$ASHFALL_QUIET" ]] && [[ "$SHLVL" -le 2 ]]; then
  print -P "%F{#4a443a}── ashfall ── %F{#6e6657}$(date '+%a %d %b %H:%M')%F{#4a443a} ── %F{#8b5a3c}${$(readlink ~/ctf/current 2>/dev/null):t:-no active challenge}%f"
fi

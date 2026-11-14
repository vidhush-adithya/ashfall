# ASHFALL — zsh layer (sourced from ~/.zshrc). Safe to edit.
export EDITOR=nvim
export CTF="$HOME/ctf"
export WL=/usr/share/seclists
export ROCKYOU=/usr/share/wordlists/rockyou.txt
export PATH="$HOME/.local/bin:$PATH"
export BAT_THEME=ansi
export FZF_DEFAULT_OPTS="--color=bg:#0c0b09,bg+:#2a2620,fg:#a89f8c,fg+:#c2b8a3,hl:#9a8348,hl+:#ad9659,border:#4a443a,prompt:#8b5a3c,pointer:#8b5a3c,marker:#5d6a48,info:#6e6657 --border=sharp --height=40%"

# ── history: huge, shared between terminals, timestamped ──
HISTFILE=~/.zsh_history; HISTSIZE=200000; SAVEHIST=200000
setopt share_history extended_history hist_ignore_all_dups hist_ignore_space \
       hist_reduce_blanks hist_verify hist_expire_dups_first
# ── navigation: type a folder name to cd; cd remembers where you were ──
setopt autocd auto_pushd pushd_ignore_dups pushd_silent interactive_comments \
       no_beep
DIRSTACKSIZE=20

bindkey -e
# keys kitty sends: Home/End/Delete, Ctrl+←/→ word jumps, Ctrl+Backspace
bindkey '^[[H' beginning-of-line '^[[F' end-of-line
bindkey '^[[1;5D' backward-word '^[[1;5C' forward-word '^H' backward-kill-word
# Ctrl+X Ctrl+E: edit the current command in nvim (great for long one-liners)
autoload -Uz edit-command-line; zle -N edit-command-line; bindkey '^X^E' edit-command-line
# Esc Esc: put sudo in front of the current (or last) command
_ashfall_sudo() { [[ -z $BUFFER ]] && BUFFER="$(fc -ln -1)"; [[ $BUFFER == sudo\ * ]] && BUFFER="${BUFFER#sudo }" || BUFFER="sudo $BUFFER"; CURSOR=${#BUFFER}; }
zle -N _ashfall_sudo; bindkey '\e\e' _ashfall_sudo
# Alt+C at the prompt: copy the current command line to the clipboard
_ashfall_copyline() { printf '%s' "$BUFFER" | wl-copy && zle -M "copied"; REGION_ACTIVE=0; }
zle -N _ashfall_copyline; bindkey '\ec' _ashfall_copyline
# Ctrl+A: select the whole command line, like a text box. Then:
#   type → replaces it · Backspace/Delete → clears it · Alt+C → copies it
#   Ctrl+A again → unselect and jump to the start of the line (the old Ctrl+A)
zle_highlight=(region:bg=#3a352c,fg=#c2b8a3)
_ashfall_select_all() {
  if (( REGION_ACTIVE )); then REGION_ACTIVE=0; CURSOR=0
  else MARK=0; CURSOR=${#BUFFER}; REGION_ACTIVE=1; fi
}
_ashfall_backspace()   { if (( REGION_ACTIVE )); then zle kill-region; REGION_ACTIVE=0; else zle backward-delete-char; fi; }
_ashfall_delete()      { if (( REGION_ACTIVE )); then zle kill-region; REGION_ACTIVE=0; else zle delete-char; fi; }
_ashfall_self_insert() { if (( REGION_ACTIVE )); then zle kill-region; REGION_ACTIVE=0; fi; zle .self-insert; }
_ashfall_paste()       { if (( REGION_ACTIVE )); then zle kill-region; REGION_ACTIVE=0; fi; zle .bracketed-paste; }
zle -N _ashfall_select_all; zle -N _ashfall_backspace; zle -N _ashfall_delete
zle -N self-insert _ashfall_self_insert; zle -N bracketed-paste _ashfall_paste
bindkey '^A' _ashfall_select_all '^?' _ashfall_backspace '^[[3~' _ashfall_delete

# ── completion: menu, colours, descriptions, typo-tolerant ──
fpath=(/usr/share/zsh/site-functions $fpath)
autoload -Uz compinit && compinit -d ~/.cache/zcompdump
command -v dircolors >/dev/null && eval "$(dircolors -b)"
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%F{#8b5a3c}── %d ──%f'
zstyle ':completion:*:warnings' format '%F{#6e6657}no matches%f'
zstyle ':completion:*' squeeze-slashes true
zstyle ':completion:*' use-cache on; zstyle ':completion:*' cache-path ~/.cache/zcompcache
zstyle ':completion:*:*:kill:*' menu yes select; zstyle ':completion:*:kill:*' force-list always
zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=38;2;139;90;60'

# ── plugins (order matters: highlighting, then substring search) ──
for p in /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh \
         /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh \
         /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh; do
  [ -f "$p" ] && source "$p"
done
# Up/Down: search history for commands starting with what you've typed
if (( $+widgets[history-substring-search-up] )); then
  bindkey '^[[A' history-substring-search-up '^[OA' history-substring-search-up
  bindkey '^[[B' history-substring-search-down '^[OB' history-substring-search-down
  HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='fg=#c2b8a3,bold,bg=#2a2620'
  HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='fg=#7a3329,bold'
  HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1
fi
# muted syntax colours (default ones are too bright for ASHFALL)
(( ${+ZSH_HIGHLIGHT_STYLES} )) || typeset -gA ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[command]='fg=#9a8348'; ZSH_HIGHLIGHT_STYLES[builtin]='fg=#9a8348'
ZSH_HIGHLIGHT_STYLES[alias]='fg=#9a8348'; ZSH_HIGHLIGHT_STYLES[function]='fg=#9a8348'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#a0523f,bold'; ZSH_HIGHLIGHT_STYLES[precommand]='fg=#8b5a3c,underline'
ZSH_HIGHLIGHT_STYLES[path]='fg=#a89f8c,underline'; ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#74825d'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#74825d'; ZSH_HIGHLIGHT_STYLES[comment]='fg=#4a443a'
# "command not found" → tells you which package has it
[ -f /usr/share/doc/pkgfile/command-not-found.zsh ] && source /usr/share/doc/pkgfile/command-not-found.zsh
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

# ── quality of life ──────────────────────────────────────
alias ..='cd ..' ...='cd ../..' ....='cd ../../..'
alias d='dirs -v | head -10'                      # recent folders; jump with  cd -2
alias rm='rm -I' cp='cp -i' mv='mv -i'            # ask before clobbering
alias ports='sudo ss -tulpn'                      # what's listening
alias please='sudo $(fc -ln -1)'                  # rerun last command with sudo
alias h='history 1 | tail -40' path='print -l $path'
alias reload='exec zsh'
mkcd()  { mkdir -p "$1" && cd "$1"; }
venv()  { [ -d .venv ] || python3 -m venv .venv; source .venv/bin/activate; }
bak()   { cp -a "$1" "$1.bak.$(date +%Y%m%d-%H%M%S)"; }
# list small folders automatically after cd
chpwd() { (( $(command ls -A | wc -l) <= 40 )) && { command -v eza >/dev/null && eza --group-directories-first || command ls --color=auto; }; }

# ── long commands: desktop notification when they finish ──
# (nmap, hashcat, ffuf... start one, switch away, get pinged)
ASHFALL_NOTIFY_AFTER=${ASHFALL_NOTIFY_AFTER:-30}
_ashfall_preexec() { _ashfall_cmd=$1; _ashfall_t0=$EPOCHSECONDS; }
_ashfall_precmd() {
  local rc=$? dt
  [[ -z $_ashfall_t0 ]] && return
  dt=$(( EPOCHSECONDS - _ashfall_t0 )); unset _ashfall_t0
  (( dt >= ASHFALL_NOTIFY_AFTER )) || return
  local what=${_ashfall_cmd[1,60]}
  if (( rc == 0 )); then notify-send -a ASHFALL "done in ${dt}s" "$what" 2>/dev/null
  else notify-send -a ASHFALL -u critical "failed ($rc) after ${dt}s" "$what" 2>/dev/null; fi
}
zmodload zsh/datetime
autoload -Uz add-zsh-hook
add-zsh-hook preexec _ashfall_preexec
precmd_functions=(_ashfall_precmd ${precmd_functions:#_ashfall_precmd})  # run first, so it sees the real exit code

# ── ctf: record a terminal session for your writeup ──────
# ctflog → everything you type and see is saved in the challenge's logs/ folder; type exit to stop
ctflog() {
  local dir="${PWD}"; [ -d ~/ctf/current ] && dir=~/ctf/current
  mkdir -p "$dir/logs"; local f="$dir/logs/session-$(date +%Y%m%d-%H%M%S).log"
  echo "recording → $f   (exit to stop)"; ASHFALL_QUIET=1 script -q -f "$f"
}

# ── help: list every ASHFALL shell helper ────────────────
ashfall-help() {
  print -P "%F{#8b5a3c}── keys ──%f"
  print "  Tab menu · ↑/↓ history search · Ctrl+R fuzzy history · Ctrl+T find file"
  print "  Ctrl+A select all (again: line start) · Alt+C copy line · Esc Esc add sudo · Ctrl+X Ctrl+E edit in nvim"
  print "  → accept suggestion · Ctrl+Alt+A copy ALL terminal output (kitty)"
  print -P "%F{#8b5a3c}── navigation ──%f"
  print "  c  ..  ...  d  cd -N  z <name>  mkcd <dir>"
  print -P "%F{#8b5a3c}── ctf ──%f"
  print "  cn notes myip nmapq nmapf fuzzdir vhosts serve listen revsh triage flagfind ex ctflog"
  print "  b64d b64e hexd hexe rot13 urld urle jwtd"
  print -P "%F{#8b5a3c}── misc ──%f"
  print "  ports please venv bak h path reload   (long commands >${ASHFALL_NOTIFY_AFTER}s notify you)"
}

# ── greeting ─────────────────────────────────────────────
if [[ -o interactive ]] && [[ -z "$ASHFALL_QUIET" ]] && [[ "$SHLVL" -le 2 ]]; then
  _cur=$(readlink ~/ctf/current 2>/dev/null); _cur=${_cur:t}
  print -P "%F{#4a443a}── ashfall ── %F{#6e6657}$(date '+%a %d %b %H:%M')%F{#4a443a} ── %F{#8b5a3c}${_cur:-no active challenge}%f  %F{#4a443a}(ashfall-help)%f"
  unset _cur
fi

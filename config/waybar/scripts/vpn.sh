#!/usr/bin/env bash
# Shows the CTF VPN address (HTB/THM openvpn = tun0, wireguard = wg0)
for i in tun0 tun1 wg0; do
  ip=$(ip -4 -o addr show "$i" 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
  if [ -n "$ip" ]; then
    printf '{"text":"VPN %s","class":"up","tooltip":"%s %s · click to copy"}\n' "$ip" "$i" "$ip"
    exit 0
  fi
done
printf '{"text":"VPN ---","class":"down","tooltip":"no tunnel up"}\n'

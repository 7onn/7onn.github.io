---
title: "Kubernetes management tooling"
date: 2025-07-21T22:00:00+02:00
tags: [engineering, kubernetes, devops, sre]
author: Tom M G
draft: false
---

## Introduction
Managing Kubernetes clusters means interacting with dozens/hundreds/thousands of resources on a daily basis. These can be quite cumbersome to deal with and the amount of commands to memorize is insanely extensive. To alleviate this load, I'll describe here what I use to make this easier.

## Fubectl
[This](https://github.com/kubermatic/fubectl) brings many nice aliases that will speed things up in terms of typing;

My highlighted ones are
1. `k`
	* Shorter for kubectl
2. `kcs`
	* Change active cluster e.g. docker-desktop,staging,production
3. `kcns`
	* Change active namespace e.g. default,service-a,service-b

It does also bring important variables `$(kube_ctx_namespace)` that can be used in PS1 for showing the current context and namespace.

## PS1
This is extremely helpful to display on your terminal, before you run any command, what's the context in which you would run it. e.g.
```bash
# "staging" is the cluster set by "kcs"
# "default" is the namespace set by "kcns"
/Users/tom/dev/7onn.github.io  main ± ⛵staging/default Montag 2025-07-21 22:11:30 +0200
$ kubectl --help
...
```

There are easy solutions that can display these information for you like [p10k](https://github.com/romkatv/powerlevel10k) or [starship](https://starship.rs). But if you are looking for a low overhead on your terminal performance, here's how I do [it](https://github.com/7onn/osdot/blob/main/.zsh/ps1.zsh).

Or simply add this to you `.zshrc`

```bash
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
WHITE="\033[0;37m"
RESET="\033[0m"
PURPLE="\033[38;5;183m"

function dir_ps1() {
  echo -e "${PURPLE}⭐$(pwd)${RESET}"
}

function git_ps1() {
  branch=$(git branch 2>/dev/null | sed -n '/^\*/s/^\* //p')
  if [[ -n "$branch" ]]; then
    if [[ -n "$(git diff --name-only HEAD)" ]]; then
      echo -e "${YELLOW}\UE0A0 ${branch} ±${RESET}
"
    else
      echo -e "${YELLOW}\UE0A0 ${RESET}${branch}${RESET}
"
    fi
  fi
}

function kube_ps1() {
  local ctx="$(kube_ctx_name)"
  if [[ -n "$ctx" ]]; then
    local ns="$(kube_ctx_namespace)"
    if [[ "$ctx" == *"production"* ]]; then
      echo -e "${RED}⛵${ctx}${RESET}/${CYAN}${ns}${RESET}"
    else
      echo -e "${GREEN}⛵${ctx}${RESET}/${CYAN}${ns}${RESET}"
    fi
  fi
}


function _update_ps1() {
  PS1="%1 
$(dir_ps1) $(git_ps1) $(kube_ps1) $(date +'%A %Y-%m-%d %H:%M:%S %z')
$ "
}

autoload -Uz add-zsh-hook
add-zsh-hook precmd _update_ps1
```

imho, the nicest thing on this PS1 is that it prints "production" in red color to decrease your chances of running things in the wrong place.

# K9s
[This](https://github.com/derailed/k9s) will help you to things quickly like e.g. jump through resources, switch between apps' logs, port-forward, describe, edit, and delete.

My highlighted commands are

1. Check most resource consuming pods
```bash
$ k9s -A
...
# Type :pods to search pods
# Type SHIFT+C to sort by CPU
# Type SHIFT+M to sort by Memory
```

2. Check logs
```bash
$ k9s
...
# Type :pods, :deploy, :sts, :ds, :cj, or :job to search for workloads
# Type "l" over the selected workload
# Type "w" to print the whole log line
```

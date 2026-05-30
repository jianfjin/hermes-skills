# Bridge Pitfalls

## pitfall: tmux local username is jin, not jianfjin

The local machine (jin-X555LAB) username differs from the VM username. All tmux injection and SSH-to-local commands must use `jin@localhost`, NOT `jianfjin@localhost`.

Discovered 2026-05-19 when `ssh -p 2222 jianfjin@localhost` returned `Permission denied` but `ssh -p 2222 jin@localhost` succeeded. The SSH key was correctly authorized on the local machine — it was a username mismatch between VM (jianfjin) and local (jin).

Verify with: `ssh -p 2222 jin@localhost "whoami"` → should print `jin`.
